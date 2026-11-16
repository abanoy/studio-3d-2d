"""Record small source-only catalogue for a design; no tools/runtimes/Git."""
from pathlib import Path
import hashlib
import json

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
ANCHORS={
    'src/character_height.gd':['static func query','const SIX_FEET'],
    'src/import_height_review.gd':['func start','func prepare','func apply','func release_scratch'],
    'src/import_actions.gd':['var offer_height','func placement','func add'],
    'src/model.gd':['static func definition','static func scale_valid','static func validate','func apply('],
    'src/renderer.gd':['func prepare_model'],
    'src/world_runtime.gd':['static func prepare','func restore_instances'],
    'src/import_placement.gd':['static func local_bounds','static func plan'],
    'src/app.gd':['func append_object(','func append_object_data'],
    'src/pose_editor.gd':['func add_model','func apply_scale'],
    'src/storage.gd':['static func readable_manifest','static func save_project','static func decode_project'],
    'src/has_project.gd':['func save_asset','func import_asset','func _finish_open'],
    'src/asset_package.gd':['static func snapshot','static func import_into'],
    'tools/has_project.py':['def members'],
    'src/sequence_graph.gd':['static func error'],
    'tools/sequence_graph.py':['def error('],
    'src/extended_timing.gd':['static func required','static func unwrap','static func child_schema'],
    'tools/extended_timing.py':['def required','def unwrap','def child_schema'],
    'src/root_component_document.gd':['static func validate','static func promote'],
    'src/shape_comparison.gd':['func prepare'],
    'src/wind_helper_candidate.gd':['static func import_actor'],
    'src/wind_review.gd':['func begin_preview'],
    'src/secondary_helper_editor.gd':['func install'],
    'src/pose_thumbnail.gd':['static func'],
    'src/airflow.gd':['static func world_transform'],
    'src/physics_rig.gd':['static func create'],
    'src/physics_prop.gd':['static func create'],
    'src/secondary_live.gd':['static func create'],
    'src/secondary_spring.gd':['static func create'],
    'src/source_secondary.gd':['const SOURCE_SCALE','static func create'],
    'src/source_bone_bindings.gd':['static func resolve'],
    'src/recovery.gd':['static func checkpoint','static func persist_checkpoint'],
    'tests/character_height_smoke.gd':[],
    'tests/height_import_native_smoke.gd':[],
    'tests/height_fixture.gd':[],
    'tests/verify_character_height.py':[],
    'tests/test_has_project.py':[],
    'tests/test_asset_package.py':[],
    'tests/test_extended_timing.py':[],
    'tests/test_sequence_graph.py':[],
}


def main():
    files={}
    for name,anchors in ANCHORS.items():
        body=(ROOT/name).read_bytes();lines=body.decode('utf-8').splitlines()
        hits={anchor:[index+1 for index,line in enumerate(lines) if anchor in line] for anchor in anchors}
        files[name]={'sha256':hashlib.sha256(body).hexdigest(),'bytes':len(body),'anchors':hits}
    (HERE/'SOURCE_READS.json').write_text(json.dumps({'format':'six_foot_plan_source_catalogue_1','source_only':True,'files':files},indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'source_files':len(files),'missing_anchor_spellings':{name:[key for key,value in row['anchors'].items() if not value] for name,row in files.items() if any(not value for value in row['anchors'].values())}}))


if __name__=='__main__':main()
