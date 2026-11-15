"""CPU-only private oracle preparation; never imports/launches Godot or app code."""
from pathlib import Path
import argparse,ast,hashlib,json,math,os,stat,struct,subprocess,sys,time
sys.dont_write_bytecode=True
from oracle_math import I,require,mm,mv,trs
R=Path(__file__).resolve().parents[2];CODE=Path(__file__).resolve().parent
B=R/'output/sfm-bone-bindings-native-launch-20261114T033026205/run/Studio/output/compatibility/source-1794627119-888-34370685'
MDL='8da09c905227ddc8eef73a3f83594a4eb1c3a6d5304ee41ba5471bef834bc716';GLB='4e6ac7c2a7a84dea4b46b0bcb5724af68781243f57737e555b4cc82f2628b90d';SCALE=.01905
sha=lambda b:hashlib.sha256(b).hexdigest()
def stamp(p):
 for ancestor in [p,*p.parents]:
  info=ancestor.lstat();require(not stat.S_ISLNK(info.st_mode)and not getattr(info,'st_file_attributes',0)&0x400,'Reparse input refused')
 p=p.resolve(strict=True);s=p.stat();data=p.read_bytes();t=p.stat();require((s.st_size,s.st_mtime_ns)==(t.st_size,t.st_mtime_ns),'changed while read');return {'path':str(p),'bytes':len(data),'mtime_ns':s.st_mtime_ns,'sha256':sha(data)}
def save(p,v):
 with p.open('x',encoding='utf-8',newline='\n')as f:json.dump(v,f,ensure_ascii=True,separators=(',',':'),allow_nan=False);f.write('\n')
def main():
 for name in ['oracle_math.py','prepare_private_oracle.py','run_headless_transport.py']:ast.parse((CODE/name).read_text(encoding='utf-8-sig'),filename=name)
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path);opt=ap.parse_args();out=(opt.output or CODE/('private-preparation-'+time.strftime('%Y%m%dT%H%M%SZ',time.gmtime()))).resolve();require(out.is_relative_to(CODE)and not out.exists(),'fresh owned prep directory required');out.mkdir()
 params=json.loads((B/'parameters.json').read_bytes());req=json.loads((B/'conversion-request.json').read_bytes());native=Path(req['source']);raw=native.read_bytes();require(sha(raw)==MDL and sha((B/'scene.glb').read_bytes())==GLB,'fixture identity');count,start=struct.unpack_from('<II',raw,156);require(count==69,'69 bones only');parents=[];locals=[];lengths={}
 for i in range(count):
  at=start+216*i;parent=struct.unpack_from('<i',raw,at+4)[0];p=struct.unpack_from('<3f',raw,at+32);q=struct.unpack_from('<4f',raw,at+44);parents.append(parent);locals.append(trs([v*SCALE for v in p],q));kind,rel=struct.unpack_from('<II',raw,at+164)
  if kind==5:lengths[i]=struct.unpack_from('<f',raw,at+rel+4)[0]
 require(len(lengths)==49 and parents[18]==17 and parents[27]==26,'expected measured parent chains');cross=params['native_parameters']['source_export_crosswalk'];require(cross['native_mdl_sha256']==MDL and cross['source_scale']==SCALE,'crosswalk context')
 axes=[(1.,0.,0.),(0.,1.,0.),(0.,0.,1.)];poses=[{'id':'rest','rows':[]}]
 def row(index,axis,sign,translation=False):
  angle=sign*.23;q=[v*math.sin(angle/2)for v in axis]+[math.cos(angle/2)];return {'native_index':index,'position':[sign*.031*v for v in axis]if translation else[0.,0.,0.],'rotation_xyzw':[0.,0.,0.,1.]if translation else q}
 for index in[8,17,18,26,27]:
  for ai,axis in enumerate(axes):
   for sign in[-1,1]:poses.append({'id':'rotate_%d_%s_%s'%(index,'XYZ'[ai],'neg'if sign<0 else'pos'),'rows':[row(index,axis,sign)]})
 for index in[17,26]:
  for ai,axis in enumerate(axes):
   for sign in[-1,1]:poses.append({'id':'move_parent_%d_%s_%s'%(index,'XYZ'[ai],'neg'if sign<0 else'pos'),'rows':[row(index,axis,sign,True)]})
 for parent,child in[(17,18),(26,27)]:
  for ai,axis in enumerate(axes):
   for sign in[-1,1]:poses.append({'id':'combined_%d_%d_%s_%s'%(parent,child,'XYZ'[ai],'neg'if sign<0 else'pos'),'rows':[row(parent,axis,sign),row(child,axis,-sign)]})
 roots=[];axis=[.3,.7,-.2];n=math.sqrt(sum(v*v for v in axis));q=[v/n*math.sin(.47/2)for v in axis]+[math.cos(.47/2)]
 for scale in[1.,2.]:
  roots.append({'id':'root_identity_scale_%d'%scale,'position':[0.,0.,0.],'rotation_xyzw':[0.,0.,0.,1.],'scale':scale});roots.append({'id':'root_moved_rotated_scale_%d'%scale,'position':[.37,-.22,.41],'rotation_xyzw':q,'scale':scale})
 C=[1.,0.,0.,0.,0.,0.,1.,0.,0.,-1.,0.,0.,0.,0.,0.,1.];cases=[]
 for root in roots:
  W=trs(root['position'],root['rotation_xyzw'],[root['scale']]*3)
  for pose in poses:
   lookup={r['native_index']:r for r in pose['rows']};local=[]
   for i in range(count):
    a=locals[i].copy()
    if i in lookup:
     r=lookup[i];rotation=trs([0.,0.,0.],r['rotation_xyzw']);a=mm(a,rotation)
     for j in range(3):a[4*j+3]+=r['position'][j]
    local.append(a)
   global_m={}
   def compose(i):
    if i not in global_m:global_m[i]=mm(compose(parents[i]),local[i])if parents[i]>=0 else local[i]
    return global_m[i]
   bones=[mm(W,mm(C,compose(i)))for i in range(count)];tips=[{'native_index':i,'expected_position':mv(bones[i],[0.,0.,length*SCALE])}for i,length in sorted(lengths.items())]
   cases.append({'id':root['id']+'__'+pose['id'],'root':root,'pose':pose['rows'],'expected_world_bones':bones,'expected_native_Z_tips':tips,'root_scale':root['scale']})
 fixture={'format':'has_private_native_transport_oracle_1','glb_path':str(B/'scene.glb'),'glb_sha256':GLB,'parameters_sha256':sha((B/'parameters.json').read_bytes()),'native_mdl_sha256':MDL,'source_conversion_scale':SCALE,'rest_by_root_id':{case['root']['id']:case['expected_world_bones'] for case in cases if case['id'].endswith('__rest')},'expected_bindings':69,'expected_rule_count':49,'cases':cases,'rule_lengths':[{'native_index':i,'length_scaled':length*SCALE}for i,length in sorted(lengths.items())]};save(out/'PRIVATE_ORACLE.json',fixture)
 files=[p for p in(R/'src').rglob('*')if p.is_file()and p.suffix!='.pyc'and'__pycache__'not in p.parts]+[R/n for n in['run.py','project.godot','main.tscn']]+[CODE/n for n in['oracle_math.py','prepare_private_oracle.py','headless_transport.gd','run_headless_transport.py']]+[native,native.with_suffix('.vvd'),B/'scene.glb',B/'parameters.json',out/'PRIVATE_ORACLE.json',Path(r'C:\a\tools\Godot\Godot_v4.6-stable_win64.exe'),Path(sys.executable)]
 lock={'format':'has_private_headless_transport_input_lock_1','status':'PREPARED_NOT_LAUNCHED','root':str(R),'qualified_full_revision':'f380729cb170682068017b0d4c29b5f8425cdd14','qualified_full_run':str(R/'output/windows-canonical-bone-binding-20261114T040946652'),'HEAD':subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),'created_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'private_oracle':str(out/'PRIVATE_ORACLE.json'),'source_conversion_scale':SCALE,'root_scales':[1.,2.],'files':[stamp(p)for p in sorted(set(files))]};save(out/'INPUT_LOCK.json',lock)
 public={'format':'has_headless_transport_preparation_1','status':'UNPARSED_UNRUN_WAITING_ROOT_LEASE','source_conversion_scales_qualified':[SCALE],'model_root_uniform_scales_to_measure':[1.,2.],'native_actuator_indices':[8,17,18,26,27],'parent_child_pairs':[[17,18],[26,27]],'signed_rotation_axes':['X','Y','Z'],'pose_cases':len(poses),'root_cases':len(roots),'configurations':len(cases),'expected_bone_world_comparisons':len(cases)*69,'expected_native_Z_tip_comparisons':len(cases)*49,'expected_skeleton_global_rest_comparisons':len(cases)*69,'expected_total_checks':8+len(cases)*(69+69+49+2),'parent_motion_semantics':'Skeleton bone-local offsets atnative17and26; attached world-object parenting is not measured','per_case_reset_required':True,'posed_vertex_render_or_skin_transport':'UNRUN_NOT_MEASURED_BY_THIS_SKELETON_PROBE','unmodified_actual_apis':['pose_editor.definition','scene3d.load_glb','model.inventory','model.check_bindings','source_bone_bindings.resolve','model.apply','model.bone_transform','Skeleton3D.get_bone_rest/get_bone_pose/get_bone_global_rest'],'private_fixture_sha256':sha((out/'PRIVATE_ORACLE.json').read_bytes()),'input_lock_sha256':sha((out/'INPUT_LOCK.json').read_bytes()),'main_changed':False,'apps_launched':False,'headless_runtime_launched':False,'dynamics_added':False,'root_lease_required_before_even_parse':True};save(out/'PUBLIC_PREPARATION.json',public);print(json.dumps({'folder':str(out),'public':public,'private_fixture_bytes':(out/'PRIVATE_ORACLE.json').stat().st_size}))
if __name__=='__main__':main()
