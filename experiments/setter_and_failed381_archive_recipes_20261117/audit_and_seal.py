"""Source/payload-selection audit only; never import or run archive builder."""
from pathlib import Path
import ast
import hashlib
import json

HERE=Path(__file__).resolve().parent
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()


def reject_arrays(value):
    if isinstance(value,dict):
        forbidden={'vertex_positions','corner_normals','setter_payload','initial_vertices','initial_corner_indices','source_raw_vertex_indices','source_lod0_vertex_indices','image_data','audio_data','base64'}
        for key,item in value.items():
            assert not (key in forbidden and item),key
            assert not (key in {'vertices','indices','triangles'} and isinstance(item,(list,dict))),key
            reject_arrays(item)
    elif isinstance(value,list):
        for item in value:reject_arrays(item)


def main():
    assert not (HERE/'INDEX.json').exists()
    plan=json.loads((HERE/'INPUTS.json').read_bytes())
    source=(HERE/'build_archive.py').read_text(encoding='utf-8')
    tree=ast.parse(source);compile(tree,str(HERE/'build_archive.py'),'exec')
    imports={alias.name for node in tree.body if isinstance(node,ast.Import) for alias in node.names}
    assert imports=={'argparse','gzip','hashlib','json'}
    assert len(plan['plans']['setter'])==25 and len(plan['plans']['failed381'])==42
    checked=[]
    for kind,rows in plan['plans'].items():
        assert len(rows)==len({row['archive_path'] for row in rows})
        for row in rows:
            path=Path(plan['roots'][row['root']])/row['path']
            assert not path.name.startswith('PRIVATE') and sha(path)==row['sha256'] and path.stat().st_size==row['bytes']
            if path.suffix=='.json':reject_arrays(json.loads(path.read_bytes()))
            checked.append(kind+':'+row['archive_path'])
    assert plan['private_native_arrays_or_private_logs_read'] is False
    assert sum(row['archive_path'].startswith('actual/receipts/') for row in plan['plans']['failed381'])==27
    assert 'recipe_payloads' not in source or 'index' in source
    assert "for row in index['files']:" in source and "gzip.decompress(body)==raw" in source
    assert 'not target.exists()' in source and "target.mkdir(exist_ok=False)" in source
    audit={'format':'has_setter_failed381_archive_recipe_source_audit_1','passed':True,'exact_inputs_checked':len(checked),
        'checked_inputs':checked,'no_native_array_or_private_log_payload_selected':True,'builder_parsed_compiled_only':True,
        'builder_imported_or_executed':False,'engine_CIM_or_Git_executed':False,'separate_archive_cases':True}
    (HERE/'SOURCE_AUDIT.json').write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8')
    files=[]
    for path in sorted(HERE.iterdir()):
        if path.is_file():
            assert path.suffix in {'.py','.json','.md'}
            files.append({'path':path.name,'bytes':path.stat().st_size,'sha256':sha(path)})
    index={'format':'has_source_experiment_index_1','packet':HERE.name,'files':files,'file_count':len(files),
        'bytes':sum(row['bytes'] for row in files),'excludes':['INDEX.json'],'actual_archives_created':False,'private_native_arrays_or_logs_included':False}
    (HERE/'INDEX.json').write_text(json.dumps(index,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'index_sha256':sha(HERE/'INDEX.json'),'builder_sha256':sha(HERE/'build_archive.py'),'inputs_sha256':sha(HERE/'INPUTS.json'),
        'exact_inputs_checked':len(checked),'recipe_files':len(files),'recipe_bytes':index['bytes'],'builder_executed':False}))


if __name__=='__main__':main()
