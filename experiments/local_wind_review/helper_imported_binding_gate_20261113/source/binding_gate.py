"""Pure completeness/transfer checks for actual imported source-node snapshots."""
import copy,hashlib,json,math,struct

def require(ok,message):
    if not ok:raise ValueError(message)

def encoded(value):return json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False).encode()
def digest(value):return hashlib.sha256(encoded(value)).hexdigest()

def inventory(doc):
    nodes=doc.get("nodes",[]);require(isinstance(nodes,list) and 0<len(nodes)<=100000,"Node inventory missing")
    parents={}
    for index,node in enumerate(nodes):
        require(isinstance(node,dict),"Node declaration")
        for child in node.get("children",[]):
            require(type(child)is int and 0<=child<len(nodes) and child not in parents,"Ambiguous node parent")
            parents[child]=index
    roots=doc.get("scenes",[])[doc.get("scene",0)]["nodes"];active=set();pending=list(roots)
    while pending:
        node=pending.pop();require(type(node)is int and 0<=node<len(nodes),"Active node index")
        require(node not in active,"Cycle or duplicate active traversal")
        active.add(node);pending.extend(nodes[node].get("children",[]))
    declared=set();skin_joints=set()
    def ref(value):
        require(type(value)is int and 0<=value<len(nodes),"Declared node reference")
        declared.add(value)
    for skin in doc.get("skins",[]):
        for node in skin.get("joints",[]):ref(node);skin_joints.add(node)
        if "skeleton"in skin:ref(skin["skeleton"])
    ex=doc.get("extensions",{});v1=ex.get("VRMC_springBone",{});v0=ex.get("VRM",{}).get("secondaryAnimation",{})
    additions=doc.get("extras",{}).get("has_secondary_helpers_1",{})
    for declaration in (v1,additions):
        for spring in declaration.get("springs",[]):
            for joint in spring.get("joints",[]):ref(joint["node"])
            if spring.get("center")is not None and spring.get("center")!=-1:ref(spring["center"])
        for collider in declaration.get("colliders",[]):ref(collider["node"])
    for group in v0.get("boneGroups",[]):
        for node in group.get("bones",[]):ref(node)
        if group.get("center")is not None and group.get("center")!=-1:ref(group["center"])
    for group in v0.get("colliderGroups",[]):ref(group["node"])
    rows=[{"source_node":i,"parent":parents.get(i,-1),"children":node.get("children",[]),"mesh":node.get("mesh",-1),"skin":node.get("skin",-1),"active":i in active,"declared_reference":i in declared,"skin_joint":i in skin_joints}for i,node in enumerate(nodes)]
    morphs=[]
    for index in sorted(active):
        node=nodes[index]
        if "mesh"not in node:continue
        mesh=doc.get("meshes",[])[node["mesh"]];counts={len(p.get("targets",[]))for p in mesh.get("primitives",[])}
        require(len(counts)<=1,"Inconsistent declared morph target counts")
        count=next(iter(counts),0)
        if not count:continue
        weights=node.get("weights",mesh.get("weights",[0.]*count))
        require(isinstance(weights,list) and len(weights)==count and all(type(v)in(int,float) and math.isfinite(v)for v in weights),"Declared morph default inventory")
        morphs.append({"source_node":index,"target_count":count,"source_weights":weights})
    return {"node_count":len(nodes),"nodes":rows,"required_nodes":sorted(active|declared),"skin_joints":sorted(skin_joints),"morphs":morphs}

def matrix(value):return isinstance(value,list) and len(value)==16 and all(type(v)in(int,float) and math.isfinite(v) and abs(v)<1e8 for v in value)

def validate_shapes(snapshot,expected,requested):
    require(isinstance(requested,dict) and requested.get("format")=="studio_source_shape_2" and type(requested.get("enabled"))is bool and isinstance(requested.get("overrides"),dict),"Requested static shape contract")
    require(snapshot.get("shape")==requested,"Requested static morph setting differs")
    rows=snapshot.get("shapes");require(isinstance(rows,list),"Observed static morph rows missing")
    actual={r.get("source_node"):r for r in rows if isinstance(r,dict)}
    require(len(actual)==len(rows) and set(actual)=={r["source_node"]for r in expected["morphs"]},"Complete static morph node coverage differs")
    available={str(r["source_node"]):r["target_count"]for r in expected["morphs"]}
    for key,weights in requested["overrides"].items():
        require(key in available and isinstance(weights,dict),"Unknown reviewed morph node")
        for target,weight in weights.items():require(isinstance(target,str) and target.isdigit() and str(int(target))==target and int(target)<available[key] and type(weight)in(int,float) and math.isfinite(weight),"Unknown reviewed morph target/value")
    for row in expected["morphs"]:
        weights=list(row["source_weights"])if requested["enabled"]else[0.]*row["target_count"]
        for key,value in requested["overrides"].get(str(row["source_node"]),{}).items():weights[int(key)]=value
        observed=actual[row["source_node"]]
        require(observed.get("effective_weights")==weights,"Effective static morph weights differ")
        floats=[struct.unpack("<f",struct.pack("<f",value))[0]for value in weights]
        require(observed.get("actual_weights")==floats,"Actual imported static morph weights differ")
    return True

def validate_snapshot(snapshot,expected,glb_sha,requested_shape):
    require(isinstance(snapshot,dict) and snapshot.get("format")=="has_actual_imported_bindings_1","Snapshot format")
    require(snapshot.get("problems")==[],"Actual imported snapshot problems")
    validate_shapes(snapshot,expected,requested_shape)
    require(snapshot.get("glb_sha256")==glb_sha and snapshot.get("node_count")==expected["node_count"],"Snapshot source/node count")
    require(snapshot.get("source_node_audit")==expected["nodes"],"Complete source-node inventory correspondence differs")
    require(not snapshot.get("secondary_error"),"Imported secondary declarations unsupported: "+str(snapshot.get("secondary_error")))
    table=snapshot.get("bindings");require(isinstance(table,dict),"Binding table missing")
    runtime=set();nonoffset=set()
    for key,row in table.items():
        require(isinstance(key,str) and key.isdigit() and str(int(key))==key and 0<=int(key)<expected["node_count"],"Noncanonical source-node key")
        require(isinstance(row,dict) and type(row.get("source_node"))is int and row.get("source_node")==int(key) and row.get("source_parent")==expected["nodes"][int(key)]["parent"],"Binding source-node/parent correspondence")
        require(row.get("kind")in("bone","node","offset") and isinstance(row.get("id"),str) and row["id"],"Binding kind/id")
        require(matrix(row.get("base")) and matrix(row.get("global_base")),"Full finite base matrices required")
        require(isinstance(row.get("runtime_identity"),str) and row["runtime_identity"] and row["runtime_identity"]not in runtime,"Runtime binding alias")
        runtime.add(row["runtime_identity"])
        if row["kind"]!="offset":require(row["id"]not in nonoffset,"Imported bone/node identity alias");nonoffset.add(row["id"])
        if int(key)in expected["skin_joints"]:require(row["kind"]=="bone","Declared skin joint is not an actual bone")
    missing=set(expected["required_nodes"])-{int(k)for k in table}
    require(not missing,"Incomplete original/declared coverage: "+str(sorted(missing)))
    for key,row in table.items():
        if row["kind"]=="bone":
            parent=row["source_parent"]
            while parent>=0 and table.get(str(parent),{}).get("kind")!="bone":parent=expected["nodes"][parent]["parent"]
            require(row.get("runtime_parent_source_node")==parent,"Actual bone parent/source-node join differs")
        if row["kind"]=="offset":
            parent=table.get(str(row["source_parent"]))
            require(parent is not None and parent["kind"]=="bone" and parent["id"]==row["id"],"Offset must use its explicit actual parent bone")
            require(row.get("runtime_attachment_parent_source_node")==row["source_parent"],"Offset actual BoneAttachment parent differs")
            require(row.get("observed_node_local")==row["base"] and row.get("offset_composed_global")==row["global_base"],"Offset actual local/parent composition differs")
            if expected["nodes"][int(key)]["declared_reference"]:require("secondary_offset_matrix"in row,"Declared offset lacks actual secondary descriptor")
            if "secondary_offset_matrix"in row:require(row["secondary_offset_matrix"]==row["base"],"Secondary offset descriptor base differs")
    observed={int(row["source_node"]):row["status"]for row in snapshot.get("coverage",[])}
    require(len(snapshot.get("coverage",[]))==expected["node_count"] and len(observed)==expected["node_count"] and set(observed)==set(range(expected["node_count"])) and all(observed[i]==("mapped"if str(i)in table else "unmapped")for i in observed),"Complete observed coverage ledger differs")
    return copy.deepcopy(table)

def transfer(source,candidate,source_inventory,candidate_inventory,source_sha,candidate_sha,protocol,requested_shape):
    original=validate_snapshot(source,source_inventory,source_sha,requested_shape)
    derived=validate_snapshot(candidate,candidate_inventory,candidate_sha,requested_shape)
    count=source_inventory["node_count"]
    require(candidate_inventory["node_count"]>=count,"Candidate lost original nodes")
    for i in range(count):
        old=source_inventory["nodes"][i];new=candidate_inventory["nodes"][i]
        require(all(old[k]==new[k]for k in("source_node","parent","mesh","skin","active","skin_joint")),"Retained source-node identity differs")
    mapped=protocol.imported_binding_map(original,derived)
    for key in original:
        if original[key]["kind"]=="bone":require(original[key]["runtime_parent_source_node"]==derived[key]["runtime_parent_source_node"],"Retained actual bone parent changed")
        require(original[key]["global_base"]==derived[key]["global_base"],"Imported retained global base changed")
    helpers=[i for i in range(count,candidate_inventory["node_count"])]
    require(all(str(i)in derived for i in helpers),"Added helper lacks actual imported identity")
    return {"format":"has_actual_imported_binding_transfer_1","original_nodes":count,"original_bound_nodes":len(original),"original_required_nodes":len(source_inventory["required_nodes"]),"candidate_nodes":candidate_inventory["node_count"],"added_helper_nodes":helpers,"bindings":mapped,"new_helpers":{str(i):derived[str(i)]for i in helpers},"source_inventory_sha256":digest(source_inventory),"candidate_inventory_sha256":digest(candidate_inventory),"scope":"Actual import binding/base preservation only; no live-body, UI, physics or native fidelity acceptance"}
