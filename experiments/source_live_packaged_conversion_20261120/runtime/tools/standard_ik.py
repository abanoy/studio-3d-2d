"""Bounded standard-node CCD evaluator; output is ordinary local FK pose data."""
import math
from mathutils import Euler,Matrix,Quaternion,Vector

FORMAT="studio_ik_constraints_1"


def local_matrix(node):
    if "matrix" in node:
        values=node["matrix"]
        if len(values)!=16:raise ValueError("Invalid joint matrix")
        return Matrix([values[c::4] for c in range(4)])
    x,y,z,w=node.get("rotation",[0,0,0,1])
    return Matrix.LocRotScale(Vector(node.get("translation",[0,0,0])),Quaternion((w,x,y,z)),Vector(node.get("scale",[1,1,1])))


class Solver:
    def __init__(self,asset):
        self.nodes=asset.doc.get("nodes",[])
        self.descriptor=asset.doc.get("asset",{}).get("extras",{}).get("studio_ik_constraints",{})
        self.parents={}
        for i,node in enumerate(self.nodes):
            for child in node.get("children",[]):
                if type(child) is not int or not 0<=child<len(self.nodes) or child in self.parents:raise ValueError("Invalid standard IK hierarchy")
                self.parents[child]=i
        self.rest=[local_matrix(node) for node in self.nodes]
        self.joints={i for skin in asset.doc.get("skins",[]) for i in skin.get("joints",[])}
        self.names={}
        for i in self.joints:self.names.setdefault(self.nodes[i].get("name",""),[]).append(i)
        if not self.descriptor:return
        if self.descriptor.get("format")!=FORMAT or not isinstance(self.descriptor.get("chains"),list) or len(self.descriptor["chains"])>64:
            raise ValueError("Invalid standard IK declarations")
        work=0
        for chain in self.descriptor["chains"]:
            for key in ("controller","effector"):
                self.index(chain[key])
            if type(chain["iterations"]) is not int or not 1<=chain["iterations"]<=256 or not 0<chain["angle_limit"]<=math.tau:
                raise ValueError("Invalid standard IK work settings")
            if not 1<=len(chain["links"])<=32:raise ValueError("Invalid standard IK links")
            prior=chain["effector"];seen=set()
            for link in chain["links"]:
                self.index(link["node"])
                if link["node"] in seen or link["node"]==prior or not self.ancestor(link["node"],prior):raise ValueError("IK links must follow the effector's ancestor chain")
                if self.ancestor(link["node"],chain["controller"]):raise ValueError("IK target cannot descend from its solved links")
                seen.add(link["node"]);prior=link["node"]
                if "minimum" in link or "maximum" in link:
                    for field in ("minimum","maximum"):
                        if len(link.get(field,[]))!=3 or any(not math.isfinite(v) or abs(v)>math.tau*2 for v in link[field]):raise ValueError("Invalid standard IK limits")
                    if any(a>b for a,b in zip(link["minimum"],link["maximum"])):raise ValueError("Reversed standard IK limits")
            work+=chain["iterations"]*len(chain["links"])
        if work>32768:raise ValueError("Standard IK exceeds its per-pose work budget")

    def index(self,index):
        if type(index) is not int or not 0<=index<len(self.nodes) or index not in self.joints:raise ValueError("Invalid standard IK joint")

    def ancestor(self,parent,node):
        seen=set()
        while True:
            if node==parent:return True
            if node not in self.parents:return False
            if node in seen or len(seen)>256:raise ValueError("Cyclic or excessive IK hierarchy")
            seen.add(node);node=self.parents[node]

    def apply(self,records,base=(),enabled=None):
        if not self.descriptor:return dict(bones=records,chains=[],skipped=[],available=False)
        enabled=enabled or {};values={};output={};changed=set();cache={}
        def bind(record):
            ids=self.names.get(record["name"],[])
            if len(ids)!=1:raise ValueError("Ambiguous IK pose binding: "+record["name"])
            x,y,z,w=record["rotation_xyzw"]
            values[ids[0]]=(Vector(record["translation"]),Quaternion((w,x,y,z)).normalized())
            return ids[0]
        for record in base:bind(record)
        affected=set()
        for record in records:affected.add(bind(record));output[record["name"]]=dict(record)
        def global_matrix(node,active=None):
            if node in cache:return cache[node]
            active=set() if active is None else active
            if node in active or len(active)>256:raise ValueError("Cyclic IK pose hierarchy")
            active.add(node)
            local=self.rest[node]
            if node in values:
                position,rotation=values[node]
                local=local@Matrix.LocRotScale(position,rotation,Vector((1,1,1)))
            cache[node]=global_matrix(self.parents[node],active)@local if node in self.parents else local.copy()
            active.remove(node)
            return cache[node]
        reports=[]
        def limit(rotation,link):
            if "minimum" not in link:return rotation
            angles=rotation.to_euler("XYZ")
            return Euler(tuple(min(hi,max(lo,value)) for value,lo,hi in zip(angles,link["minimum"],link["maximum"])),"XYZ").to_quaternion()
        for chain in self.descriptor["chains"]:
            active=chain["name"] in enabled or any(node==chain["controller"] or (self.ancestor(node,chain["effector"])!=self.ancestor(node,chain["controller"])) for node in affected)
            if not active:continue
            if not enabled.get(chain["name"],True):
                for link in chain["links"]:
                    values.setdefault(link["node"],(Vector((0,0,0)),Quaternion()));changed.add(link["node"])
                reports.append(dict(name=chain["name"],residual=0.,minimum_residual=0.,steps=0,method="disabled",enabled=False))
                continue
            goal=global_matrix(chain["controller"]).translation.copy()
            for link in chain["links"]:
                node=link["node"];position,rotation=values.get(node,(Vector((0,0,0)),Quaternion()))
                values[node]=(position,limit(rotation,link));changed.add(node)
            cache.clear();steps=0;warm=False
            # A two-link hinge can be seeded by its geometric bend. This avoids
            # very slow CCD convergence from an almost straight knee. Each joint
            # still obeys the declared angle step and local limits.
            if len(chain["links"])==2:
                knee,hip=chain["links"]
                free=[i for i in range(3) if "minimum" in knee and abs(knee["maximum"][i]-knee["minimum"][i])>1e-8]
                if len(free)==1:
                    axis_index=free[0]
                    h=global_matrix(hip["node"]).translation;k=global_matrix(knee["node"]).translation;f=global_matrix(chain["effector"]).translation
                    a=(k-h).length;b=(f-k).length;distance=(goal-h).length
                    if min(a,b)>1e-8:
                        bend=math.pi-math.acos(min(1.,max(-1.,(a*a+b*b-distance*distance)/(2*a*b))))
                        current=math.acos(min(1.,max(-1.,(k-h).normalized().dot((f-k).normalized()))))
                        sign=-1 if knee["maximum"][axis_index]<=0 else 1
                        angle=max(-chain["angle_limit"],min(chain["angle_limit"],sign*(bend-current)))
                        axis=Vector((int(axis_index==0),int(axis_index==1),int(axis_index==2)))
                        position,rotation=values[knee["node"]]
                        values[knee["node"]]=(position,limit((rotation@Quaternion(axis,angle)).normalized(),knee));cache.clear();steps+=1
                        world=global_matrix(hip["node"]);inverse=world.to_3x3().normalized().inverted()
                        source=inverse@(global_matrix(chain["effector"]).translation-h);target=inverse@(goal-h)
                        if min(source.length,target.length)>1e-8:
                            rotation_delta=source.normalized().rotation_difference(target.normalized())
                            angle=min(rotation_delta.angle,chain["angle_limit"])
                            position,rotation=values[hip["node"]]
                            values[hip["node"]]=(position,limit((rotation@Quaternion(rotation_delta.axis,angle)).normalized(),hip));cache.clear();steps+=1
                            warm=True
            for _ in range(chain["iterations"]-int(warm)):
                if (global_matrix(chain["effector"]).translation-goal).length<1e-6:break
                for link in chain["links"]:
                    node=link["node"];world=global_matrix(node)
                    inverse=world.to_3x3().normalized().inverted()
                    a=inverse@(global_matrix(chain["effector"]).translation-world.translation)
                    b=inverse@(goal-world.translation)
                    if min(a.length,b.length)<1e-9:continue
                    a.normalize();b.normalize()
                    free=[i for i in range(3) if "minimum" not in link or abs(link["maximum"][i]-link["minimum"][i])>1e-8]
                    if len(free)==1:
                        axis=Vector((int(free[0]==0),int(free[0]==1),int(free[0]==2)))
                        a-=axis*a.dot(axis);b-=axis*b.dot(axis)
                        if min(a.length,b.length)<1e-9:continue
                        a.normalize();b.normalize();angle=math.atan2(axis.dot(a.cross(b)),min(1.,max(-1.,a.dot(b))))
                    else:
                        dot=min(1.,max(-1.,a.dot(b)));axis=a.cross(b)
                        angle=math.atan2(axis.length,dot)
                        if angle<1e-9:continue
                        if axis.length<1e-9:
                            axis=a.cross(Vector((1,0,0)) if abs(a.x)<.9 else Vector((0,1,0)))
                        axis.normalize()
                    angle=min(chain["angle_limit"],max(-chain["angle_limit"],angle))
                    position,rotation=values.get(node,(Vector((0,0,0)),Quaternion()))
                    values[node]=(position,limit((rotation@Quaternion(axis,angle)).normalized(),link))
                    changed.add(node);cache.clear();steps+=1
            residual=(global_matrix(chain["effector"]).translation-goal).length
            minimum_residual=0.
            if len(chain["links"])==1:
                origin=global_matrix(chain["links"][0]["node"]).translation
                minimum_residual=abs((global_matrix(chain["effector"]).translation-origin).length-(goal-origin).length)
            reports.append(dict(name=chain["name"],residual=residual,minimum_residual=minimum_residual,steps=steps,method="two_link_ccd" if warm else "ccd",enabled=True))
        for node in changed:
            native=self.nodes[node].get("name","")
            if len(self.names.get(native,[]))!=1:raise ValueError("Ambiguous solved joint name")
            position,rotation=values[node]
            output[native]=dict(name=native,translation=list(position),rotation_xyzw=[rotation.x,rotation.y,rotation.z,rotation.w])
        return dict(bones=list(output.values()),chains=reports,skipped=self.descriptor.get("skipped",[]),available=True)
