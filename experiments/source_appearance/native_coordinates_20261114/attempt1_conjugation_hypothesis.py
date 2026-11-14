"""Independent stdlib native-MDL/VVD to glTF rest/skin coordinate measurement.
No production imports, executable model content, runtime or dynamics. Output has
hashes, counts, errors and numeric index joins only; no private coordinate arrays.
"""
from pathlib import Path
from itertools import permutations, product
from collections import defaultdict
import hashlib,json,math,struct,sys,time
sys.dont_write_bytecode=True
R=Path.cwd().resolve();O=R/'output/native-jiggle-coordinate-proof-20261114'
B=R/'output/sfm-bone-bindings-native-launch-20261114T033026205/run/Studio/output/compatibility/source-1794627119-888-34370685'
EXPECTED_MDL='8da09c905227ddc8eef73a3f83594a4eb1c3a6d5304ee41ba5471bef834bc716'
EXPECTED_GLB='4e6ac7c2a7a84dea4b46b0bcb5724af68781243f57737e555b4cc82f2628b90d'
SCALE=0.01905;EPS=2e-5;I=[1.,0.,0.,0.,0.,1.,0.,0.,0.,0.,1.,0.,0.,0.,0.,1.]
sha=lambda b:hashlib.sha256(b).hexdigest()
compact=lambda v:json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def require(ok,why):
 if not ok:raise ValueError(why)
def mm(a,b):return [sum(a[4*r+k]*b[4*k+c] for k in range(4)) for r in range(4) for c in range(4)]
def mv(a,v,w=1.):return [sum(a[4*r+k]*v[k] for k in range(3))+a[4*r+3]*w for r in range(3)]
def inv(a):
 rows=[list(a[4*r:4*r+4])+I[4*r:4*r+4] for r in range(4)]
 for c in range(4):
  pivot=max(range(c,4),key=lambda r:abs(rows[r][c]));require(abs(rows[pivot][c])>1e-14,'singular matrix');rows[c],rows[pivot]=rows[pivot],rows[c];f=rows[c][c];rows[c]=[v/f for v in rows[c]]
  for r in range(4):
   if r!=c:
    f=rows[r][c];rows[r]=[x-f*y for x,y in zip(rows[r],rows[c])]
 return [v for r in rows for v in r[4:]]
def maximum(a,b):return max(abs(x-y) for x,y in zip(a,b))
def norm(v):return math.sqrt(sum(x*x for x in v))
def dist(a,b):return norm([x-y for x,y in zip(a,b)])
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def col(a,c):return [a[4*r+c] for r in range(3)]
def det(a):return a[0]*(a[5]*a[10]-a[6]*a[9])-a[1]*(a[4]*a[10]-a[6]*a[8])+a[2]*(a[4]*a[9]-a[5]*a[8])
def quality(a):
 cols=[col(a,c) for c in range(3)];lengths=[norm(c) for c in cols]
 return {'determinant':det(a),'maximum_unit_column_error':max(abs(v-1) for v in lengths),'nonuniform_column_ratio':max(lengths)/min(lengths),'maximum_column_dot':max(abs(dot(cols[x],cols[y])) for x,y in [(0,1),(0,2),(1,2)]),'affine_row_error':maximum(a[12:],I[12:])}
def trs(t,q,s=(1.,1.,1.)):
 x,y,z,w=q;n=norm(q);require(abs(n-1)<1e-4,'nonunit quaternion');x,y,z,w=[v/n for v in q]
 a=[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w),t[0],2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w),t[1],2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y),t[2],0.,0.,0.,1.]
 for r in range(3):
  for c in range(3):a[4*r+c]*=s[c]
 return a
def cm_to_rm(a):return [a[4*c+r] for r in range(4) for c in range(4)]
def angular(a,b):return math.degrees(math.acos(max(-1.,min(1.,dot(a,b)/(norm(a)*norm(b))))))
# Known rigid/nonrigid controls are independent of any native input.
control_rotation=trs((2.,3.,4.),(math.sqrt(.5),0.,0.,math.sqrt(.5)))
require(maximum(mm(control_rotation,inv(control_rotation)),I)<1e-12,'inverse control')
require(dist(mv(control_rotation,(0.,1.,0.)),(2.,3.,5.))<1e-12,'quaternion/control handedness')
control_scaled=I.copy();control_scaled[5]=2.;control_reflected=I.copy();control_reflected[0]=-1.;control_shear=I.copy();control_shear[1]=.1
require(quality(control_scaled)['nonuniform_column_ratio']>1.9 and quality(control_reflected)['determinant']<0 and quality(control_shear)['maximum_column_dot']>.09,'nonrigid refusal controls')
params_raw=(B/'parameters.json').read_bytes();params=json.loads(params_raw);meta=params['native_parameters'];cross=meta['source_export_crosswalk'];req=json.loads((B/'conversion-request.json').read_bytes());native_path=Path(req['source']);raw=native_path.read_bytes();glb=(B/'scene.glb').read_bytes();vvd=native_path.with_suffix('.vvd').read_bytes()
require(sha(raw)==EXPECTED_MDL and sha(glb)==EXPECTED_GLB,'input SHA differs');require(cross['native_mdl_sha256']==EXPECTED_MDL and cross['glb_sha256']==EXPECTED_GLB and cross['source_scale']==SCALE and params['scale']==SCALE,'crosswalk identities/scale')
require(raw[:4]==b'IDST' and struct.unpack_from('<i',raw,4)[0]==49 and struct.unpack_from('<I',raw,76)[0]==len(raw),'MDL header')
count,start=struct.unpack_from('<II',raw,156);require(count==69 and start>=408 and start+count*216<=len(raw),'MDL table');native=[];rule_lengths={}
for i in range(count):
 at=start+216*i;name_rel,parent=struct.unpack_from('<ii',raw,at);vals=struct.unpack_from('<7f',raw,at+32);end=raw.find(b'\0',at+name_rel);name=raw[at+name_rel:end].decode('ascii');require(all(math.isfinite(x) for x in vals),'nonfinite native');require(-1<=parent<count and parent!=i,'native parent');native.append({'parent':parent,'name':name,'local':trs([v*SCALE for v in vals[:3]],vals[3:])})
 kind,rel=struct.unpack_from('<II',raw,at+164)
 if kind==5:rule_lengths[i]=struct.unpack_from('<f',raw,at+rel+4)[0]
require(set(rule_lengths)=={r['native_bone_index'] for r in meta['source_jiggle']['rules']} and len(rule_lengths)==49,'rule/native mapping')
for r in meta['source_jiggle']['rules']:require(r['parameters']['length']==rule_lengths[r['native_bone_index']],'native rule length mismatch')
require(glb[:4]==b'glTF' and struct.unpack_from('<II',glb,4)==(2,len(glb)),'GLB header');chunks=[];offset=12
while offset<len(glb):
 length,kind=struct.unpack_from('<II',glb,offset);require(length%4==0 and offset+8+length<=len(glb),'GLB chunk bounds');chunks.append((kind,glb[offset+8:offset+8+length]));offset+=8+length
require([k for k,_ in chunks]==[0x4e4f534a,0x004e4942],'GLB chunks');g=json.loads(chunks[0][1]);binary=chunks[1][1];require(len(g['buffers'])==1 and 'uri' not in g['buffers'][0] and g['buffers'][0]['byteLength']<=len(binary)<=g['buffers'][0]['byteLength']+3,'GLB buffer')
node_local=[];parents={}
for i,n in enumerate(g['nodes']):
 require(not ('matrix'in n and any(k in n for k in ['translation','rotation','scale'])),'mixed matrix/TRS');a=cm_to_rm(n['matrix']) if 'matrix'in n else trs(n.get('translation',(0.,0.,0.)),n.get('rotation',(0.,0.,0.,1.)),n.get('scale',(1.,1.,1.)));require(len(a)==16 and all(math.isfinite(v) for v in a),'bad node matrix');node_local.append(a)
 for c in n.get('children',[]):require(type(c)is int and 0<=c<len(g['nodes']) and c not in parents,'GLTF parent');parents[c]=i
G={};N={}
def global_node(i,trail=()):
 require(i not in trail,'GLTF cycle')
 if i not in G:G[i]=mm(global_node(parents[i],(*trail,i)),node_local[i]) if i in parents else node_local[i]
 return G[i]
def global_native(i,trail=()):
 require(i not in trail,'native cycle')
 if i not in N:N[i]=mm(global_native(native[i]['parent'],(*trail,i)),native[i]['local']) if native[i]['parent']>=0 else native[i]['local']
 return N[i]
joined={r['native_index']:r for r in cross['bones']};require(set(joined)==set(range(count)) and len({r['gltf_node_index'] for r in joined.values()})==count,'crosswalk bijection')
for i,r in joined.items():require(r['native_parent_index']==native[i]['parent'] and r['native_name']==native[i]['name'],'native/crosswalk catalogue');global_native(i);global_node(r['gltf_node_index'])
# Search all proper signed axis permutations independently, including reflections
# as negative controls. Select using translations, then test complete bases.
axes=[]
for perm in permutations(range(3)):
 for signs in product((-1.,1.),repeat=3):
  a=I.copy()
  for r in range(3):
   for c in range(3):a[4*r+c]=signs[r] if c==perm[r] else 0.
  err=max(dist(mv(a,col(N[i],3)),col(G[joined[i]['gltf_node_index']],3)) for i in joined)
  axes.append((err,perm,signs,a))
proper=sorted((x for x in axes if det(x[3])>0),key=lambda x:x[0]);reflected=sorted((x for x in axes if det(x[3])<0),key=lambda x:x[0]);error,perm,signs,C=proper[0];Ci=inv(C)
require(error<EPS and sum(x[0]<EPS for x in proper)==1,'no unique common proper axis conversion')
corrections={i:mm(inv(N[i]),mm(Ci,G[joined[i]['gltf_node_index']])) for i in joined}
rest_errors={i:maximum(G[joined[i]['gltf_node_index']],mm(C,mm(N[i],Ci))) for i in joined};left_errors={i:maximum(G[joined[i]['gltf_node_index']],mm(C,N[i])) for i in joined}
q=[quality(G[r['gltf_node_index']]) for r in joined.values()];q_native=[quality(v) for v in N.values()]
require(max(rest_errors.values())<EPS,'common conjugation failed');require(all(v['determinant']>0 and v['maximum_unit_column_error']<EPS and v['nonuniform_column_ratio']<1+EPS and v['maximum_column_dot']<EPS and v['affine_row_error']<EPS for v in q),'nonrigid or reflected actual node')
# glTF accessors: bounds/stride/type checked directly, no production decoder.
formats={5121:('B',1),5123:('H',2),5125:('I',4),5126:('f',4)};widths={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16};access_cache={}
def accessor(index):
 if index in access_cache:return access_cache[index]
 a=g['accessors'][index];require('sparse'not in a and not a.get('normalized',False) and a['componentType']in formats,'unsupported accessor');f,size=formats[a['componentType']];width=widths[a['type']];view=g['bufferViews'][a['bufferView']];require(view.get('buffer',0)==0,'external buffer');base=view.get('byteOffset',0)+a.get('byteOffset',0);stride=view.get('byteStride',size*width);require(stride>=size*width and base+(a['count']-1)*stride+size*width<=view.get('byteOffset',0)+view['byteLength']<=len(binary),'accessor bounds');values=[struct.unpack_from('<'+f*width,binary,base+i*stride) for i in range(a['count'])];require(all(math.isfinite(v) for row in values for v in row),'nonfinite accessor');access_cache[index]=values;return values
skins=[];joint_native={r['gltf_node_index']:i for i,r in joined.items()};closure=[];ibm_errors=[];join_rows=[]
for si,skin in enumerate(g['skins']):
 ibms=[cm_to_rm(x) for x in accessor(skin['inverseBindMatrices'])];require(len(ibms)==len(skin['joints'])==count and set(skin['joints'])==set(joint_native),'complete skin joint domain');slot_native=[joint_native[n] for n in skin['joints']];skins.append((ibms,slot_native))
 for slot,ni in enumerate(slot_native):
  memberships=joined[ni]['skin_memberships'];require({'skin_index':si,'joint_slot':slot}in memberships,'skin slot crosswalk');e=maximum(mm(G[joined[ni]['gltf_node_index']],ibms[slot]),I);closure.append(e);expected_ibm=inv(mm(C,mm(N[ni],Ci)));ibm_errors.append(maximum(ibms[slot],expected_ibm));join_rows.append({'native_index':ni,'gltf_node_index':joined[ni]['gltf_node_index'],'skin_index':si,'joint_slot':slot,'rest_max_error':rest_errors[ni],'inverse_bind_closure_max_error':e})
require(max(closure)<EPS and max(ibm_errors)<EPS,'inverse bind closure failed')
# Parse exact native VVD vertices as a second independent neutral geometry oracle.
h=struct.unpack_from('<4s3I8I4I',vvd,0);require(h[0]==b'IDSV' and h[1]==4 and h[2]==struct.unpack_from('<I',raw,8)[0] and h[3]==1 and h[12]==0,'unsupported VVD header/fixups');vcount=h[4];vstart=h[14];require(vcount==9661 and vstart+48*vcount<=len(vvd),'VVD count bounds');source_vertices=[];buckets=defaultdict(list);step=1e-5
for i in range(vcount):
 at=vstart+48*i;weights=struct.unpack_from('<3f',vvd,at);bones=struct.unpack_from('<3B',vvd,at+12);active=vvd[at+15];pos=struct.unpack_from('<3f',vvd,at+16);normal=struct.unpack_from('<3f',vvd,at+28);uv=struct.unpack_from('<2f',vvd,at+40);require(1<=active<=3 and all(0<=bones[j]<count for j in range(active)),'VVD influence domain');wm={bones[j]:weights[j] for j in range(active) if weights[j]!=0.};p=mv(C,[v*SCALE for v in pos]);n=mv(C,normal,0.);source_vertices.append((p,n,uv,wm));buckets[tuple(round(x/step) for x in p)].append(i)
consumed=set();geometry_errors=[];weight_errors=[];normal_errors=[];uv_errors=[];neutral_errors=[];native_neutral_errors=[];transport_errors=[];weight_sums=[];primitive_rows=[];equivalent_ambiguities=0
for node_index,node in enumerate(g['nodes']):
 if 'mesh'not in node:continue
 require('skin'in node,'unskinned target mesh');mesh_world=global_node(node_index);require(maximum(mesh_world,I)<EPS,'nonidentity mesh node unsupported');ibms,slot_native=skins[node['skin']]
 for pi,primitive in enumerate(g['meshes'][node['mesh']]['primitives']):
  require(primitive.get('mode',4)==4 and 'targets'not in primitive,'primitive scope');a=primitive['attributes'];positions=accessor(a['POSITION']);normals=accessor(a['NORMAL']);uvs=accessor(a['TEXCOORD_0']);joints=accessor(a['JOINTS_0']);weights=accessor(a['WEIGHTS_0']);require(len({len(x) for x in [positions,normals,uvs,joints,weights]})==1,'attribute counts');per_errors=[]
  for pos,normal,uv,js,ws in zip(positions,normals,uvs,joints,weights):
   require(all(type(j)is int and 0<=j<count for j in js) and all(w>=0 for w in ws),'skin weights/domain');wm=defaultdict(float)
   for j,w in zip(js,ws):
    if w:wm[slot_native[j]]+=w
   center=tuple(round(x/step) for x in pos);choices=[]
   for delta in product((-1,0,1),repeat=3):
    for vi in buckets.get(tuple(x+y for x,y in zip(center,delta)),()):
     if vi in consumed:continue
     sp,sn,suv,sw=source_vertices[vi];pe=dist(pos,sp);we=max(abs(wm.get(k,0.)-sw.get(k,0.)) for k in set(wm)|set(sw));ne=dist(normal,sn);uve=min(dist(uv,suv),dist(uv,(suv[0],1.-suv[1])))
     if pe<2e-6 and we<2e-6 and ne<2e-5 and uve<2e-6:choices.append((pe+we+ne+uve,vi,pe,we,ne,uve))
   require(choices,'no native VVD counterpart for exported vertex');choices.sort();_,vi,pe,we,ne,uve=choices[0];equivalent_ambiguities+=len(choices)>1;consumed.add(vi);geometry_errors.append(pe);weight_errors.append(we);normal_errors.append(ne);uv_errors.append(uve);weight_sums.append(abs(sum(ws)-1.))
   actual=[0.,0.,0.];native_result=[0.,0.,0.]
   for slot,w in zip(js,ws):
    if not w:continue
    ni=slot_native[slot];v=mv(mm(G[joined[ni]['gltf_node_index']],ibms[slot]),pos);u=mv(mm(C,mm(N[ni],mm(Ci,ibms[slot]))),pos)
    for c in range(3):actual[c]+=w*v[c];native_result[c]+=w*u[c]
   e=dist(actual,pos);neutral_errors.append(e);native_neutral_errors.append(dist(native_result,pos));transport_errors.append(dist(actual,native_result));per_errors.append(e)
  primitive_rows.append({'mesh_node_index':node_index,'mesh_index':node['mesh'],'primitive_index':pi,'vertex_count':len(positions),'neutral_weighted_max_distance':max(per_errors)})
require(len(primitive_rows)==4 and len(consumed)==vcount==len(neutral_errors),'complete two-mesh VVD coverage');require(max(neutral_errors)<EPS and max(native_neutral_errors)<EPS and max(transport_errors)<EPS,'neutral skin agreement')
# Source SDK forward is native local Z. Measure its actual rest transport; a
# next-child segment is reported separately and never used as a replacement.
tip_errors=[];local_y_angles=[];local_z_angles=[];child_angles=[];childless=0
for ni,length in rule_lengths.items():
 a=N[ni];actual=G[joined[ni]['gltf_node_index']];native_forward=mv(C,col(a,2),0.);local_y_angles.append(angular(native_forward,col(actual,1)));local_z_angles.append(angular(native_forward,col(actual,2)))
 expected=mv(C,[a[4*r+3]+length*SCALE*a[4*r+2] for r in range(3)]);predicted=mv(actual,mv(C,(0.,0.,length*SCALE),0.));tip_errors.append(dist(expected,predicted));children=[i for i in joined if native[i]['parent']==ni]
 if not children:childless+=1
 for child in children:
  segment=[N[child][4*r+3]-a[4*r+3] for r in range(3)]
  if norm(segment)>1e-10:child_angles.append(angular(col(a,2),segment))
require(max(tip_errors)<EPS,'native local-Z tip transport')
reference=R/'output/source-sdk-jiggle-reference-20261114';ref=json.loads((reference/'REFERENCE_HASH_CHECK.json').read_bytes());ref_pins=[]
for r in ref['files']:
 data=(reference/r['file']).read_bytes();require(sha(data)==r['sha256'],'reference hash');ref_pins.append({'file':r['file'],'sha256':r['sha256']})
cpp=(reference/'jigglebones.cpp').read_text();require('MatrixGetColumn( goalMX, 2, goalForward )'in cpp and 'goalBasePosition + jiggleInfo->length * goalForward'in cpp,'SDK local Z semantics')
summary={'format':'has_independent_native_glTF_coordinate_proof_1','status':'PASSED_GLTF_REST_ONLY','checked_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'inputs':{'native_mdl_sha256':sha(raw),'glb_sha256':sha(glb),'parameters_sha256':sha(params_raw),'native_vvd_sha256':sha(vvd),'native_vvd_checksum_matches_mdl':True,'source_scale':SCALE,'source_sdk_commit':ref['commit'],'reference_files':ref_pins},'scope':{'stdlib_only':True,'production_parser_imports':False,'native_runtime_or_apps_launched':False,'main_files_changed':False,'dynamics_implemented':False,'HAS_world_or_runtime_pose_binding':'UNRUN','plus_minus_XYZ_pose_transport':'UNRUN','two_source_scales':'UNRUN','native_solver':'NOT_IMPLEMENTED','native_arrays_published':False},'counts':{'native_bones':count,'native_jiggle_rules':len(rule_lengths),'gltf_nodes':len(g['nodes']),'skins':len(skins),'meshes':len(g['meshes']),'primitives':len(primitive_rows),'native_VVD_vertices':vcount,'exported_vertices':len(neutral_errors),'source_vertices_consumed_exactly_once':len(consumed),'attribute_equivalent_candidate_ambiguities':equivalent_ambiguities},'coordinate_conversion':{'proper_axis_candidates':len(proper),'unique_candidates_with_translation_error_below_tolerance':sum(x[0]<EPS for x in proper),'axis_map':[('+'if signs[r]>0 else '-')+'XYZ'[perm[r]] for r in range(3)],'global_position_max_distance':error,'next_best_proper_position_max_distance':proper[1][0],'best_reflected_position_max_distance':reflected[0][0],'complete_joint_basis_relation':'G_glTF = C * N_scaled_native * inverse(C), within recorded error','conjugated_rest_max_matrix_error':max(rest_errors.values()),'simple_left_multiply_only_max_matrix_error':max(left_errors.values()),'right_basis_correction_vs_common_inverse_C_max_error':max(maximum(v,Ci) for v in corrections.values()),'per_bone_extra_correction_required_at_tolerance':False,'tolerance':EPS},'matrix_domain':{'negative_determinants':sum(v['determinant']<0 for v in q),'global_determinant_min':min(v['determinant'] for v in q),'global_determinant_max':max(v['determinant'] for v in q),'maximum_unit_column_error':max(v['maximum_unit_column_error'] for v in q),'maximum_nonuniform_column_ratio':max(v['nonuniform_column_ratio'] for v in q),'maximum_column_dot':max(v['maximum_column_dot'] for v in q),'nonrigid_reflection_shear_negative_controls_passed':True},'skin':{'inverse_bind_closure_max_matrix_error':max(closure),'independent_native_inverse_bind_max_matrix_error':max(ibm_errors),'weight_sum_max_error':max(weight_sums),'neutral_GLTF_weighted_max_distance':max(neutral_errors),'neutral_native_rest_weighted_max_distance':max(native_neutral_errors),'native_vs_GLTF_weighted_max_distance':max(transport_errors),'native_VVD_scaled_axis_position_max_distance':max(geometry_errors),'native_VVD_to_GLTF_weight_max_error':max(weight_errors),'native_VVD_to_GLTF_normal_max_distance':max(normal_errors),'native_VVD_UV_agreement_allowing_V_flip_max_distance':max(uv_errors),'primitive_counts_and_errors':primitive_rows},'native_tip_direction':{'SDK_forward_column':2,'rule_count_checked':len(rule_lengths),'native_local_Z_tip_world_max_distance':max(tip_errors),'GLTF_joint_local_positive_Y_vs_native_forward_max_angle_degrees':max(local_y_angles),'GLTF_joint_local_positive_Z_wrong_axis_min_angle_degrees':min(local_z_angles),'next_native_child_segment_pairs':len(child_angles),'rules_without_native_children':childless,'next_child_segment_vs_native_Z_min_angle_degrees':min(child_angles) if child_angles else None,'next_child_segment_vs_native_Z_max_angle_degrees':max(child_angles) if child_angles else None,'interpretation':'In this exact GLTF rest export local +Y corresponds to native local +Z after the proven basis conversion. Next-child directions were measured separately; no arbitrary tail or HAS runtime axis is inferred.'},'numeric_index_joins':sorted(join_rows,key=lambda r:r['native_index']),'limitations':['This is exact-input GLTF rest and neutral-skin qualification, not actual HAS world/skeleton/posed transport.','One tested source scale. Independent plus/minus XYZ pose and two-scale app qualification remains UNRUN.','VVD transport uses complete attribute-compatible multiset coverage; equivalent repeated vertex attributes are not claimed unique native vertex identities.','No native rule dynamics, feedback, stability, render/native artist fidelity or solver acceptance.']}
p=O/'PUBLIC_CANDIDATE_AUDIT.json';p.write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n',encoding='utf-8');print(json.dumps({k:summary[k] for k in ['status','counts','coordinate_conversion','matrix_domain','skin','native_tip_direction']},allow_nan=False));print('AUDIT '+str(p)+' SHA256 '+sha(p.read_bytes()))
