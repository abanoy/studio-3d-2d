"""Prepare exact-source early-refusal hooks only; never edit main or launch."""
from pathlib import Path
import difflib
import hashlib
import json

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
PREFIX='preload("res://src/import_basis_boundary.gd")'


def main():
    recipes={
      'src/model.gd':[(
        '\tif not value is Dictionary: return "Invalid model record."',
        '\tif not value is Dictionary: return "Invalid model record."\n\tvar import_basis_error: String='+PREFIX+'.model_error(value)\n\tif not import_basis_error.is_empty():return import_basis_error')],
      'src/storage.gd':[(
        '\tvar data: Dictionary=parser.data',
        '\tvar data: Dictionary=parser.data\n\tif not '+PREFIX+'.project_error(data).is_empty():return false'),(
        '\tif not cancel_path.is_empty() and FileAccess.file_exists(cancel_path):return "Project saving cancelled. Previous save preserved."',
        '\tif not cancel_path.is_empty() and FileAccess.file_exists(cancel_path):return "Project saving cancelled. Previous save preserved."\n\tvar import_basis_error: String='+PREFIX+'.project_error({"model":model,"world":world,"sequence_graph":sequence_graph})\n\tif not import_basis_error.is_empty():return import_basis_error'),(
        'static func decode_project(data,folder: String,extended:=false,rasters=null) -> Dictionary:',
        'static func decode_project(data,folder: String,extended:=false,rasters=null) -> Dictionary:\n\tvar import_basis_error: String='+PREFIX+'.project_error(data)\n\tif not import_basis_error.is_empty():return {"error":import_basis_error}')],
      'src/renderer.gd':[(
        'func prepare_model(data: Dictionary,incoming_video: Dictionary={}) -> Dictionary:',
        'func prepare_model(data: Dictionary,incoming_video: Dictionary={}) -> Dictionary:\n\tvar import_basis_error: String='+PREFIX+'.model_error(data)\n\tif not import_basis_error.is_empty():return {"error":import_basis_error}')],
      'src/app.gd':[(
        'func append_object_data(data: Dictionary, kind: String, start_frame := 0, placement := {}) -> String:',
        'func append_object_data(data: Dictionary, kind: String, start_frame := 0, placement := {}) -> String:\n\tvar import_basis_error: String='+PREFIX+'.model_error(data)\n\tif not import_basis_error.is_empty():return import_basis_error')],
      'src/shape_comparison.gd':[(
        'func prepare() -> void:\n\tif not valid():close();return\n\tvar actor: RefCounted=editor.actor()',
        'func prepare() -> void:\n\tif not valid():close();return\n\tvar actor: RefCounted=editor.actor()\n\tvar import_basis_error: String='+PREFIX+'.model_error(actor.data)\n\tif not import_basis_error.is_empty():fail(import_basis_error);return')],
      'src/wind_review.gd':[(
        '\tvar source: RefCounted=actor();var filtered:=Groups.filter(catalog,wind_ids.keys())',
        '\tvar source: RefCounted=actor()\n\tvar import_basis_error: String='+PREFIX+'.model_error(source.data)\n\tif not import_basis_error.is_empty():fail(import_basis_error);return\n\tvar filtered:=Groups.filter(catalog,wind_ids.keys())')],
      'src/wind_helper_candidate.gd':[(
        'static func prepare(source: RefCounted,candidate_path: String,shape_snapshot: Dictionary,baseline_pose: Dictionary,video: Dictionary,operations: Array,candidate_sha256: String) -> Dictionary:',
        'static func prepare(source: RefCounted,candidate_path: String,shape_snapshot: Dictionary,baseline_pose: Dictionary,video: Dictionary,operations: Array,candidate_sha256: String) -> Dictionary:\n\tvar import_basis_error: String='+PREFIX+'.model_error(source.data if source else {})\n\tif not import_basis_error.is_empty():return error(import_basis_error)')],
      'src/secondary_helper_editor.gd':[(
        'func install(value: Dictionary) -> void:',
        'func install(value: Dictionary) -> void:\n\tvar import_basis_actor: RefCounted=actor()\n\tif import_basis_actor:\n\t\tvar import_basis_error: String='+PREFIX+'.model_error(import_basis_actor.data)\n\t\tif not import_basis_error.is_empty():info.text=import_basis_error;return')],
    }
    patch=[];records=[]
    for name,changes in recipes.items():
        p=ROOT/name;raw=p.read_bytes();source=raw.decode('utf-8');eol='\r\n'if b'\r\n'in raw else'\n';proposed=source
        converted=[]
        for old,new in changes:
            old=old.replace('\n',eol);new=new.replace('\n',eol)
            if name=='src/storage.gd'and old.startswith('\tif not cancel_path.is_empty()'):
                signature=next(line for line in source.splitlines()if line.startswith('static func save_project('))
                old=signature+eol+old;new=signature+eol+new
            assert proposed.count(old)==1,(name,old)
            proposed=proposed.replace(old,new,1);converted.append((old,new))
        restored=proposed
        for old,new in reversed(converted):
            assert restored.count(new)==1
            restored=restored.replace(new,old,1)
        assert restored==source
        records.append({'path':name,'before_bytes':len(raw),'before_sha256':hashlib.sha256(raw).hexdigest(),
            'proposed_bytes':len(proposed.encode()),'proposed_sha256':hashlib.sha256(proposed.encode()).hexdigest(),
            'insertion_count':len(changes),'inverse_recipe_restores_every_original_byte':True,
            'actual_main_still_exact':p.read_bytes()==raw})
        patch.extend(difflib.unified_diff(source.splitlines(True),proposed.splitlines(True),fromfile='a/'+name,tofile='b/'+name))
    (HERE/'PRE_ACTIVATION_GUARDS_v2.patch').write_text(''.join(patch),encoding='utf-8',newline='')
    folder=HERE/'draft/src';folder.mkdir(parents=True,exist_ok=True)
    helper=(HERE/'source_boundary_guards.gd').read_bytes()
    if(folder/'import_basis_boundary.gd').exists():assert(folder/'import_basis_boundary.gd').read_bytes()==helper
    else:(folder/'import_basis_boundary.gd').write_bytes(helper)
    result={'format':'has_six_foot_pre_activation_hooks_1','status':'UNAPPLIED_UNPARSED_UNRUN',
        'runtime_basis_activation':False,'files':records,'main_files_written':False,
        'scope':'Only early refusal for unsupported active basis. Existing absence/legacy behavior and all original source bytes are otherwise retained.',
        'full_integration_qualification':False}
    with(HERE/'PRE_ACTIVATION_SOURCE_v2.json').open('x',encoding='utf-8')as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps({'prepared':True,'source_files':len(records),'insertions':sum(x['insertion_count']for x in records),'main_writes':False}))


if __name__=='__main__':main()
