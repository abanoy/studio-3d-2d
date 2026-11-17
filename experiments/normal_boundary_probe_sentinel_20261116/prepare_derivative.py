"""Prepare source only; no Win32, Blender, process, Git or native-input execution."""
from pathlib import Path
import ast,hashlib,json
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
OLD=ROOT/'experiments/normal_boundary_probe_20261116'
SOURCE_SHA='c6002553a74e5dca4fd097d84a6392aa08c9736ccbaa3756f42fb3ddf68069b4'
INDEX_SHA='49e7f5067be896b2faab57ae41f3afb2089a94a55b9988ea35150e4227f73856'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,raw):
    with p.open('xb') as f:f.write(raw)
def save(p,value):write(p,(json.dumps(value,indent=2)+'\n').encode())
def main():
    assert sha(OLD/'INDEX.json')==INDEX_SHA and sha(OLD/'capture_blender_normals.py')==SOURCE_SHA
    old=(OLD/'capture_blender_normals.py').read_text(encoding='utf-8')
    prefix='import ctypes as C\nfrom ctypes import wintypes as W\nfrom contextlib import contextmanager\n'
    assert old.count('import sys\n')==1
    source=old.replace('import sys\n','import sys\n'+prefix,1)
    marker='if __name__ == "__main__":\n    main()\n'
    assert source.count(marker)==1
    source=source.replace(marker,(HERE/'sentinel_fragment.py.txt').read_text(encoding='utf-8')+'\nif __name__ == "__main__":\n    _main_with_placement_sentinel()\n',1)
    ast.parse(source)
    write(HERE/'capture_blender_normals.py',source.encode())
    copied=[]
    for name in ('probe_support.py','normal_metrics.py','compare_private_normals.py','stage_after_full_pass.py','test_probe_support.py'):
        write(HERE/name,(OLD/name).read_bytes());copied.append({'path':name,'sha256':sha(HERE/name),'exact_predecessor_bytes':True})
    def funcs(text):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(text).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
    before=funcs(old);after=funcs(source)
    assert all(after[n]==v for n,v in before.items())
    # Also retain the complete numerical/metadata main function exact raw text.
    start=old.index('def main():');end=old.index('\n\nif __name__ == "__main__":')
    original_main=old[start:end]
    assert source.count(original_main)==1
    save(HERE/'DERIVATION.json',{'format':'has_background_normal_sentinel_source_derivative_1',
        'status':'SOURCE_ONLY_UNEXECUTED','predecessor_index_sha256':INDEX_SHA,'predecessor_capture_sha256':SOURCE_SHA,
        'capture_sha256':sha(HERE/'capture_blender_normals.py'),'all_original_function_ASTs_exact':True,
        'original_main_raw_bytes_exact':True,'original_main_sha256':hashlib.sha256(original_main.encode()).hexdigest(),
        'original_function_names':sorted(before),'new_functions':sorted(set(after)-set(before)),'copied_core':copied,
        'Win32_API_or_Blender_executed':False,'main_source_or_private_desktop_tool_changed':False,
        'numerical_capture_export_import_or_comparison_changed':False})
    print(json.dumps({'prepared_only':True,'capture_sha256':sha(HERE/'capture_blender_normals.py'),'original_functions_exact':len(before),'copied_core_files':len(copied)}))
if __name__=='__main__':main()
