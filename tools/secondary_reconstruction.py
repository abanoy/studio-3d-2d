"""Explicit, owned flexible guides for reviewed multi-anchor source regions.

Original nodes, source vertex/morph data and native bind prefixes stay intact.
Each original influence receives its OWN parented guide: at guide rest its
palette equals that original influence under arbitrary original bone FK.
"""
from pathlib import Path
import copy,hashlib,json,math,os,struct
import secondary_helpers as H

FORMAT='studio_secondary_reconstruction_1'
MAX_REGIONS=32
MAX_SELECTED=10000


def recipe(request):
    """Translate one explicit editor selection; never infer extra surfaces."""
    if request.get('format')==FORMAT:return copy.deepcopy(request)
    if request.get('reconstruct_weights') is not True or request.get('use_existing_joints',False):
        raise ValueError('Explicit owned-weight reconstruction is required')
    item={k:copy.deepcopy(request[k]) for k in ('node','primitive','component','vertex_mask') if k in request}
    value={k:copy.deepcopy(request[k]) for k in ('source_sha256','reviewed','segments','points_in_anchor','source_morph_defaults','morph_weights') if k in request}
    value.update(format=FORMAT,regions=[item]);return value


def inverse(m):
    a,b,c,d,e,f,g,h,i=(m[k] for k in (0,4,8,1,5,9,2,6,10))
    det=a*(e*i-f*h)-b*(d*i-f*g)+c*(d*h-e*g)
    if not math.isfinite(det) or abs(det)<1e-12:raise ValueError('Singular guide attachment')
    rows=((e*i-f*h,c*h-b*i,b*f-c*e),(f*g-d*i,a*i-c*g,c*d-a*f),(d*h-e*g,b*g-a*h,a*e-b*d))
    out=list(H.IDENTITY)
    for r in range(3):
        for col in range(3):out[col*4+r]=rows[r][col]/det
        out[12+r]=-sum(out[col*4+r]*m[12+col] for col in range(3))
    return out


def split_weight(weight,fraction):
    """Partition a positive source f32 into TWO exact f32 values; never top-N."""
    bits=struct.unpack('<I',struct.pack('<f',weight))[0]
    if bits>>31 or not math.isfinite(weight) or struct.unpack('<f',struct.pack('<f',weight))[0]!=weight:
        raise ValueError('Reconstruction needs finite nonnegative float32 source weights')
    exponent=(bits>>23)&255;mantissa=(bits&0x7fffff)|(0x800000 if exponent else 0)
    quantum=exponent-150 if exponent else -149
    amount=max(0,min(mantissa,round(mantissa*max(0.,min(1.,fraction)))))
    return math.ldexp(mantissa-amount,quantum),math.ldexp(amount,quantum)


def parameter(point,controls):
    best=None
    for index,(a,b) in enumerate(zip(controls,controls[1:])):
        axis=[b[k]-a[k] for k in range(3)];length=sum(v*v for v in axis)
        if length<1e-12:raise ValueError('Reviewed guide contains a zero-length segment')
        t=max(0.,min(1.,sum((point[k]-a[k])*axis[k] for k in range(3))/length))
        distance=sum((point[k]-a[k]-t*axis[k])**2 for k in range(3))
        if best is None or distance<best[0]:best=(distance,index+t)
    return best[1]


def common_ancestor(nodes,parents):
    paths=[]
    for node in nodes:
        path=[]
        while True:
            if node in path or len(path)>512:raise ValueError('Cyclic or excessive source hierarchy')
            path.append(node)
            if node not in parents:break
            node=parents[node]
        paths.append(path)
    return next((n for n in paths[0] if all(n in p for p in paths)),None)


def prepare(source,request):
    glb=H.GLB(source)
    if not isinstance(request,dict) or request.get('format')!=FORMAT or request.get('source_sha256')!=glb.sha:
        raise ValueError('A matching explicit reconstruction recipe is required')
    regions=request.get('regions');count=request.get('segments',4)
    if not isinstance(regions,list) or not 1<=len(regions)<=MAX_REGIONS or type(count) is not int or not 2<=count<=8:
        raise ValueError('Choose1–32 reviewed regions and2–8 guide segments')
    parents={}
    for index,node in enumerate(glb.doc['nodes']):
        for child in node.get('children',[]):
            H.integer(child,len(glb.doc['nodes']))
            if child in parents:raise ValueError('Ambiguous source hierarchy')
            parents[child]=index
    active=set();pending=list(glb.doc['scenes'][glb.doc.get('scene',0)]['nodes'])
    while pending:
        node=pending.pop()
        if node in active:raise ValueError('Ambiguous active source scene')
        active.add(node);pending.extend(glb.doc['nodes'][node].get('children',[]))
    selected={};anchors=set();views=[];total=0
    for item in regions:
        if not isinstance(item,dict):raise ValueError('Invalid reviewed region')
        ni,pi,ci=(item.get(k) for k in ('node','primitive','component'))
        if ni not in active:raise ValueError('Hidden/inactive source nodes need a separate review')
        data,indices,_weld,_dist,_coords,_anchor,summary=H.region(glb,ni,pi,ci,vertex_mask=item.get('vertex_mask'),shape=request)
        if summary['already_rigged']:raise ValueError('Existing motion joints are kept; reconstruct an unconfigured region')
        if sum(n.get('mesh')==data[0]['mesh'] for n in glb.doc['nodes'])!=1:raise ValueError('Shared mesh instances need explicit ownership before reconstruction')
        key=(ni,pi);old=selected.setdefault(key,set())
        if old.intersection(indices):raise ValueError('Reviewed reconstruction masks overlap')
        old.update(indices);total+=len(indices)
        if total>MAX_SELECTED:raise ValueError('Reviewed reconstruction exceeds10000 selected vertices')
        for slot in (0,1):
            accessor=data[2]['attributes'].get('WEIGHTS_'+str(slot))
            if accessor is not None and glb.doc['accessors'][accessor]['componentType']!=5126:
                raise ValueError('This reconstruction profile needs original float32 weights')
        for v in indices:
            pairs=data[6][v]
            if len(pairs)>4 or len({j for j,w in pairs})!=len(pairs):
                raise ValueError('More than four or repeated source influences cannot be split losslessly within eight slots')
            anchors.update(data[3]['joints'][j] for j,w in pairs if w>0)
        views.append((item,data,indices,summary))
    anchor=request.get('anchor_node',common_ancestor(sorted(anchors),parents))
    if type(anchor) is not int or any(anchor not in data[3]['joints'] for _,data,_,_ in views):
        raise ValueError('Choose one reference attachment present in every selected skin')
    frames={}
    for _item,data,_indices,_summary in views:
        joints=data[3]['joints'];reference_inverse=inverse(data[7][joints.index(anchor)])
        for source_node in anchors:
            if source_node not in joints:continue
            frame=H.multiply(data[7][joints.index(source_node)],reference_inverse)
            if source_node in frames and any(abs(a-b)>1e-6 for a,b in zip(frame,frames[source_node])):
                raise ValueError('Selected skins have incompatible shared guide bind frames; review them as separate groups')
            frames[source_node]=frame
    points=[];fractions=[];reviewed_positions={}
    for item,data,indices,summary in views:
        _data,_sel,weld,dist,coords,_j,_summary=H.region(glb,item['node'],item['primitive'],item['component'],anchor,vertex_mask=item.get('vertex_mask'),shape=request)
        span=max(dist.values())
        for v in indices:
            points.append(coords[v]);fractions.append(dist[weld[v]]/span)
            reviewed_positions[(item['node'],item['primitive'],v)]=coords[v]
    controls=request.get('points_in_anchor')
    if controls is None:
        controls=[]
        for index in range(count+1):
            order=sorted(range(len(points)),key=lambda v:abs(fractions[v]-index/count))
            near=order[:max(3,sum(abs(t-index/count)<=.08 for t in fractions))]
            controls.append([sum(points[v][k] for v in near)/len(near) for k in range(3)])
    if not isinstance(controls,list) or len(controls)!=count+1 or any(not isinstance(p,(list,tuple)) or len(p)!=3 for p in controls):raise ValueError('Invalid reviewed shared guide')
    controls=[[H.finite(v) for v in point] for point in controls]
    for a,b in zip(controls,controls[1:]):
        if H.distance(a,b)<1e-6:raise ValueError('Reviewed shared guide has a zero-length segment')
    added=len(anchors)*(count+1)
    if len(glb.doc['nodes'])+added>100000 or len(glb.springs())+len(anchors)>128 or len({j for s in glb.doc['skins'] for j in s['joints']})+added>512:
        raise ValueError('Owned reconstruction exceeds its node/guide/bone budget')
    parameters={key:parameter(p,controls) for key,p in reviewed_positions.items()}
    return {'glb':glb,'views':views,'selected':selected,'anchors':sorted(anchors),'reference':anchor,'controls':controls,'segments':count,'selected_vertices':total,'parameters':parameters}


def preview(source,request):
    request=recipe(request);plan=prepare(source,request);glb=plan['glb'];vertices=[];regions=[];edges=[];source_vertices=[]
    for _item,data,selected,summary in plan['views']:
        regions.append({k:summary[k] for k in ('node','primitive','component','material_name','vertices')})
        mapping={v:len(vertices)+i for i,v in enumerate(selected)}
        for v in selected:
            vertices.append([[data[3]['joints'][j],*H.point(data[7][j],data[4][v]),w] for j,w in data[6][v]]);source_vertices.append(v)
        for at in range(0,len(data[5]),3):
            tri=data[5][at:at+3]
            if all(v in mapping for v in tri):
                for a,b in zip(tri,tri[1:]+tri[:1]):edges.append((mapping[a],mapping[b]))
    first=copy.deepcopy(plan['views'][0][3]);first.update(vertices=plan['selected_vertices'],anchor_node=plan['reference'],anchor_name=glb.doc['nodes'][plan['reference']].get('name',''),length_in_anchor_units=sum(H.distance(a,b) for a,b in zip(plan['controls'],plan['controls'][1:])))
    bindings=sorted({plan['reference']}|set(plan['anchors']))
    return {'format':'studio_secondary_preview_1','mode':'reconstructed_weights','region':first,'vertices':vertices,'source_vertices':source_vertices,'selected_vertices':list(range(len(vertices))),'edges':edges,'can_apply':True,'points_in_anchor':plan['controls'],'affected_regions':regions,'added_nodes':len(plan['anchors'])*(plan['segments']+1),'added_chains':len(plan['anchors']),'anchors':[{'node':n,'name':glb.doc['nodes'][n].get('name',''),'available':n==plan['reference']} for n in bindings],'notice':'Owned reconstruction: '+str(plan['selected_vertices'])+' reviewed vertices; '+str(len(plan['anchors']))+' guide groups. Original poses remain editable. Rebuilt surfaces can differ slightly at rest; review before applying. Undo restores the original. Include outlines separately; bangs and unchecked areas are kept.'}


def build(source,output,request):
    request=recipe(request)
    if not isinstance(request,dict) or request.get('reviewed') is not True:raise ValueError('Review the complete reconstruction before creating its candidate')
    plan=prepare(source,request);glb=plan['glb'];stamp=glb.source.stat().st_mtime_ns
    nodes=glb.doc['nodes'];count=plan['segments'];controls=plan['controls'];guide_nodes={};local_controls={};skin_indices={}
    prefix='__HAS_Loose_Rebuilt_'+hashlib.sha256(json.dumps(request,sort_keys=True).encode()).hexdigest()[:12]
    for anchor in plan['anchors']:
        data=next(data for _item,data,selected,_summary in plan['views'] if anchor in data[3]['joints'])
        binds=data[7];skin=data[3];change=H.multiply(binds[skin['joints'].index(anchor)],inverse(binds[skin['joints'].index(plan['reference'])]))
        points=[H.point(change,p) for p in controls];local_controls[anchor]=points;indices=[]
        for i,p in enumerate(points):
            index=len(nodes);name=prefix+'_'+str(anchor)+'_'+str(i)
            if any(n.get('name')==name for n in nodes):raise ValueError('Owned guide identity collision')
            parent=anchor if i==0 else indices[-1];nodes[parent].setdefault('children',[]).append(index)
            nodes.append({'name':name,'translation':[p[k]-(points[i-1][k] if i else 0) for k in range(3)]});indices.append(index)
        guide_nodes[anchor]=indices
    for _item,data,_selected,_summary in plan['views']:
        skin=data[3];si=data[0]['skin']
        if si in skin_indices:continue
        old_joints=list(skin['joints']);binds=list(data[7]);mapping={}
        for anchor in plan['anchors']:
            if anchor not in old_joints:continue
            mapping[anchor]=list(range(len(skin['joints']),len(skin['joints'])+count+1));skin['joints'].extend(guide_nodes[anchor])
            for point in local_controls[anchor]:binds.append(H.multiply(H.translation([-v for v in point]),data[7][old_joints.index(anchor)]))
        skin['inverseBindMatrices']=glb.append(binds,'MAT4');skin_indices[si]=mapping
    glb.doc['buffers'][0]['byteLength']=len(glb.binary)
    changed=0
    for (ni,pi),selected in plan['selected'].items():
        data=glb.skin(ni,pi);skin=data[3];pairs=data[6];mapping=skin_indices[data[0]['skin']];common=data[7][skin['joints'].index(plan['reference'])]
        for v in selected:
            u=plan['parameters'][(ni,pi,v)];free=max(0.,min(count-1.,u-1.))
            left=min(count-1,int(free));right=min(count-1,left+1);fraction=free-left
            output_row=[]
            for joint,weight in pairs[v]:
                anchor=skin['joints'][joint];first,second=split_weight(weight,u if u<1. else fraction)
                a=joint if u<1. else mapping[anchor][left];b=mapping[anchor][0] if u<1. else mapping[anchor][right]
                if first:output_row.append((a,first))
                if second:output_row.append((b,second))
            if len(output_row)>8:raise ValueError('Lossless guide splitting exceeds eight influences; no weights were truncated')
            if pairs[v]!=output_row:changed+=1
            pairs[v]=output_row
        attributes=data[2]['attributes'];slots=8 if max(map(len,pairs))>4 or 'JOINTS_1' in attributes else 4
        for slot in range(slots//4):
            js=[];ws=[]
            for row in pairs:
                part=(row+[(0,0.)]*slots)[slot*4:slot*4+4];js.append([j for j,w in part]);ws.append([w for j,w in part])
            attributes['JOINTS_'+str(slot)]=glb.append(js,'VEC4',5123);attributes['WEIGHTS_'+str(slot)]=glb.append(ws,'VEC4')
    springs=glb.doc.setdefault('extras',{}).setdefault('has_secondary_helpers_1',{'specVersion':'1.0','springs':[]})['springs']
    created_chains=[]
    for anchor in plan['anchors']:
        chain={'name':prefix+'_'+str(anchor),'center':anchor,'joints':[{'node':n,'stiffness':1.,'dragForce':.45,'hitRadius':.005} for n in guide_nodes[anchor]]}
        springs.append(chain);created_chains.append(copy.deepcopy(chain))
    report={'format':'studio_generated_helpers_1','mode':'reconstructed_weights','source_sha256':glb.sha,'region':copy.deepcopy(plan['views'][0][3]),'regions':[copy.deepcopy(v[3]) for v in plan['views']],'helper_nodes':[n for values in guide_nodes.values() for n in values],'changed_vertices':changed,'source_skin_preserved':False,'original_nodes_retained':True,'original_bind_prefix_retained':True,'rest_source_geometry_retained':True,'native_fk_at_guide_rest':'per-original-influence parented guides; exact float32 weight partitions','method':'Explicit reviewed multi-anchor reconstruction; shared guide, no original source rewrite'}
    report.update(points_in_anchor=controls,guide_chains=created_chains,guide_prefix=prefix,reviewed_vertices=plan['selected_vertices'])
    glb.doc['buffers'][0]['byteLength']=len(glb.binary)
    encoded=json.dumps(glb.doc,separators=(',',':'),allow_nan=False).encode();encoded+=b' '*(-len(encoded)%4)
    if len(encoded)>H.MAX_JSON:raise ValueError('Candidate metadata exceeds supported budget')
    raw=struct.pack('<4sII',b'glTF',2,28+len(encoded)+len(glb.binary))+struct.pack('<II',len(encoded),0x4e4f534a)+encoded+struct.pack('<II',len(glb.binary),0x004e4942)+glb.binary
    if len(raw)>H.MAX_FILE:raise ValueError('Candidate exceeds supported file budget')
    if hashlib.sha256(glb.source.read_bytes()).hexdigest()!=glb.sha or glb.source.stat().st_mtime_ns!=stamp:raise ValueError('Original source changed while preparing reconstruction')
    target=Path(output).resolve()
    if target==glb.source or target.exists():raise ValueError('Choose a new owned candidate folder')
    target.mkdir(parents=True,exist_ok=False)
    with (target/'scene.glb').open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    (target/'helpers.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return {'glb':str(target/'scene.glb'),'report':report}


def main():
    import argparse
    parser=argparse.ArgumentParser(description='Review or create a NEW owned multi-anchor loose-part candidate. Originals are read-only.')
    parser.add_argument('source');parser.add_argument('recipe');parser.add_argument('output');parser.add_argument('--preview',action='store_true')
    args=parser.parse_args();recipe=json.loads(Path(args.recipe).read_text(encoding='utf-8'))
    result=preview(args.source,recipe) if args.preview else build(args.source,args.output,recipe)
    if args.preview:
        path=Path(args.output)
        with path.open('x',encoding='utf-8') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    else:print(json.dumps({'glb':result['glb'],'changed_vertices':result['report']['changed_vertices'],'guides':len(result['report']['helper_nodes'])}))


if __name__=='__main__':main()
