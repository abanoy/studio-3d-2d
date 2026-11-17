"""Seal source-only diagnostics; never import/execute the Godot scripts."""
from pathlib import Path
import hashlib
import json
import re

HERE=Path(__file__).resolve().parent
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert not (HERE/'INDEX.json').exists()
    proof=json.loads((HERE/'SOURCE_PROOF.json').read_bytes())
    assert proof['diagnostic_predicates32_byte_text_identical'] and proof['corrected_31_predicates_byte_text_identical']
    assert proof['remaining_predicate_strengthened_retaining_actual_click'] and proof['extra_wait_precedes_refresh_not_follows_refresh']
    assert sha(HERE/'neon_behavior_diagnostic.gd')==proof['diagnostic_script_sha256']
    assert sha(HERE/'neon_behavior_regression.gd')==proof['corrected_fixture_script_sha256']
    for name in ['neon_behavior_diagnostic.gd','neon_behavior_regression.gd']:
        source=(HERE/name).read_text(encoding='utf-8')
        assert len(re.findall(r'^\tcheck\(',source,re.M))==32
    rows=[]
    for path in sorted(HERE.rglob('*')):
        if not path.is_file():continue
        assert path.suffix in {'.gd','.py','.md','.json','.patch','.log'} and '__pycache__' not in path.parts
        rows.append({'path':path.relative_to(HERE).as_posix(),'bytes':path.stat().st_size,'sha256':sha(path)})
    index={'format':'has_source_experiment_index_1','packet':HERE.name,'files':rows,'file_count':len(rows),'bytes':sum(r['bytes'] for r in rows),
        'excludes':['INDEX.json'],'new_engine_execution_claimed':False,'main_or_candidate_source_edits':False,'owner_art_or_native_assets_included':False}
    (HERE/'INDEX.json').write_text(json.dumps(index,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'index_sha256':sha(HERE/'INDEX.json'),'diagnostic_sha256':sha(HERE/'neon_behavior_diagnostic.gd'),
        'corrected_fixture_sha256':sha(HERE/'neon_behavior_regression.gd'),'files':len(rows),'bytes':index['bytes']}))


if __name__=='__main__':main()
