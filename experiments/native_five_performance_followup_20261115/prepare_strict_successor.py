"""Remove proved duplicate strict-capture checks; source only, never apply/run."""
from pathlib import Path
import difflib
import hashlib
import json

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
INPUT=ROOT/'experiments/native_five_performance_candidate_20261115/source_secondary_strict.gd'
PIN='064c211efbb19b829defb959b6f9d0c6aeef36aa6c2af76065fda9f2b17b21be'
OLD='\tvar worlds: Dictionary = _baseline_guard.baseline_worlds(locals,prefix)'
NEW='''\t# Every local was just validated by unchanged frame64/Math.goal above.
\t# Its scale is the stamped base token admitted by the full69 guard config.
\t# Keep the prefix check and every unchanged compose/result-frame check;
\t# skip only the second identical69-local input validation pass.
\tvar prefix_error: String = Chains.frame_error(prefix)
\tif not prefix_error.is_empty(): return {"error":prefix_error}
\tvar full_worlds := {}
\tfor id in _baseline_guard._order:
\t\tvar parent: Variant = _baseline_guard._bones[id].parent
\t\tvar parent_world: Dictionary = prefix if parent == null else full_worlds[parent]
\t\tvar made: Dictionary = Chains.compose(parent_world,locals[id])
\t\tif made.has("error"): return made
\t\tfull_worlds[id] = made.frame
\tvar worlds: Dictionary = {"worlds":full_worlds}'''


def sha(body):return hashlib.sha256(body).hexdigest()


def main():
    assert sha(INPUT.read_bytes())==PIN
    old=INPUT.read_text(encoding='utf-8');code=old
    assert code.count(OLD)==1
    code=code.replace(OLD,NEW,1)
    field='var _expected_world_scales: Dictionary = {}\n'
    assert field in code;code=code.replace(field,'',1)
    start=code.index('\tvar all_order := Chains.parent_order(candidate._bone_specs)')
    end=code.index('\tcandidate._capture_configuration_stamp = ',start)
    code=code[:start]+code[end:]
    code=code.replace(',candidate._expected_world_scales','').replace(',_expected_world_scales','')
    redundant='''\t\tvar expected_size: float = _expected_world_scales[id]
\t\tif absf(float(actual_frame.scale)-expected_size) > EPS*expected_size: return {"error":"The imported hair world scale changed; turn its preview off."}
'''
    assert redundant in code;code=code.replace(redundant,'',1)
    code=code.replace('; _expected_world_scales.clear()','')
    code=code.replace('SOURCE-ONLY strict performance candidate; UNPARSED/UNRUN.','SOURCE-ONLY strict2 capture deduplication; UNPARSED/UNRUN.',1)
    assert '_expected_world_scales' not in code
    destination=HERE/'source_secondary_strict2.gd';destination.write_text(code,encoding='utf-8',newline='\n')
    (HERE/'strict2.diff').write_text(''.join(difflib.unified_diff(old.splitlines(keepends=True),code.splitlines(keepends=True),fromfile='actual_state266_strict/source_secondary.gd',tofile='source_secondary_strict2.gd')),encoding='utf-8',newline='\n')
    provenance={'format':'native_five_strict2_source_draft_1','status':'SOURCE_ONLY_UNPARSED_UNRUN_UNAPPLIED','input_strict_sha256':PIN,'strict2_sha256':sha(destination.read_bytes()),'scalar_core_changed':False,'all69_canonical_world_checks_retained':True,'removed_only':['Repeated local frame/scale checks already established by same-call frame64 and immutable config stamps.','Duplicate expected-world-scale cache/check, repeated identically by retained full69 composed-world check.'],'new_runtime_dependency':None}
    (HERE/'PROVENANCE.json').write_text(json.dumps(provenance,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(provenance,indent=2))


if __name__=='__main__':main()
