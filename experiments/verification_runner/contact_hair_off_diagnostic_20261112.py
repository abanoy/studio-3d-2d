from pathlib import Path
import json,hashlib,subprocess,sys,time
r=Path.cwd();sys.path.insert(0,str(r));from run import command
base=r/'output/contact-physics-undo-diagnosis-20261112';base.mkdir(exist_ok=False);folder=base/'run';folder.mkdir();src=(r/'tests/contact_physics_smoke.gd').read_text()
needle='\t\tphysics.hair_toggle.button_pressed=true\n'
replacement='''\t\tvar undo_before_hair: Array=app.history.duplicate(true);var redo_before_hair: Array=app.redo_history.duplicate(true);var world_before_hair: Dictionary=app.current_world().duplicate(true);var dirty_before_hair: bool=app.dirty;var bones_before_hair: Dictionary={}
\t\tfor bone_id in rig(native_id).order:
\t\t\tvar info: Dictionary=rig(native_id).bones[bone_id];bones_before_hair[bone_id]=info.skeleton.get_bone_pose(info.index)
\t\tphysics.hair_toggle.button_pressed=true
'''
assert src.count(needle)==1;src=src.replace(needle,replacement)
needle2='\t\tapp.undo();check(rig(native_id).data==before and app.history.size()==history,"hair freeze and exact contact restoration remain one Undo")\n'
replacement2='''\t\tvar changed_bones: Array=[]
\t\tfor bone_id in rig(native_id).order:
\t\t\tvar info: Dictionary=rig(native_id).bones[bone_id];var actual: Transform3D=info.skeleton.get_bone_pose(info.index)
\t\t\tif actual!=bones_before_hair[bone_id]:changed_bones.append({"id":bone_id,"before":str(bones_before_hair[bone_id]),"after":str(actual)})
\t\tvar diagnostic: Dictionary={"history_count_before":history,"history_count_after_off":app.history.size(),"history_exact_after_off":app.history==undo_before_hair,"redo_exact_after_off":app.redo_history==redo_before_hair,"data_exact_after_off":rig(native_id).data==before,"world_exact_after_off":app.current_world()==world_before_hair,"dirty_exact_after_off":app.dirty==dirty_before_hair,"bone_count":bones_before_hair.size(),"changed_bones_after_off":changed_bones,"fan_count_before":world_before_hair.objects.size(),"fan_count_after_off":app.current_world().objects.size()}
\t\tapp.undo();check(rig(native_id).data==before and app.history.size()==history,"hair freeze and exact contact restoration remain one Undo")
\t\tdiagnostic["history_count_after_old_undo"]=app.history.size();diagnostic["data_exact_after_old_undo"]=rig(native_id).data==before;diagnostic["world_count_after_old_undo"]=app.current_world().objects.size()
\t\tvar diagnostic_file:=FileAccess.open(folder.path_join("diagnostic.json"),FileAccess.WRITE);diagnostic_file.store_string(JSON.stringify(diagnostic,"  ",true,true));diagnostic_file.close()
\t\tapp.redo();diagnostic["redo_restores_preexisting_world"]=app.current_world()==world_before_hair;diagnostic["redo_restores_preexisting_history"]=app.history==undo_before_hair
\t\tdiagnostic_file=FileAccess.open(folder.path_join("diagnostic.json"),FileAccess.WRITE);diagnostic_file.store_string(JSON.stringify(diagnostic,"  ",true,true));diagnostic_file.close()
\t\tapp.free();await settled();print("CONTACT_PHYSICS_UNDO_DIAG "+JSON.stringify(diagnostic));quit(1 if failures else 0);return
'''
assert src.count(needle2)==1;src=src.replace(needle2,replacement2);script=base/'diagnostic.gd';script.write_text(src,encoding='utf-8')
args=command(str(script),extra=['--log-file',str(folder/'engine-native.log'),'--',str(folder)])
p=subprocess.run(args,cwd=r,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=160);(base/'process.log').write_text(p.stdout+p.stderr,encoding='utf-8');(base/'command.json').write_text(json.dumps(args,indent=2)+'\n',encoding='utf-8');receipt=Path(args[args.index('--receipt')+1]);(base/'receipt-path.txt').write_text(str(receipt));print(json.dumps({'exit':p.returncode,'script_sha256':hashlib.sha256(script.read_bytes()).hexdigest(),'receipt':str(receipt),'folder':str(folder)}));print((folder/'diagnostic.json').read_text() if (folder/'diagnostic.json').exists() else (p.stdout+p.stderr)[-3000:])