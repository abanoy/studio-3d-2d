"""Read-only index/AST/lineage verifier; never imports capture or Win32 APIs."""
from pathlib import Path
import ast,hashlib,json
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    index=json.loads((HERE/'INDEX.json').read_bytes())
    rows=index['files'];assert len(rows)==index['files_count'] and len({r['path'] for r in rows})==len(rows)
    actual={p.relative_to(HERE).as_posix() for p in HERE.rglob('*') if p.is_file() and p.name!='INDEX.json'}
    assert actual=={r['path'] for r in rows}
    for row in rows:
        p=HERE/row['path'];assert p.resolve().is_relative_to(HERE.resolve()) and not p.is_symlink()
        assert p.stat().st_size==row['bytes'] and sha(p)==row['sha256']
    derive=json.loads((HERE/'DERIVATION.json').read_bytes());old=HERE.parent/'normal_boundary_probe_20261116'
    assert sha(old/'INDEX.json')==derive['predecessor_index_sha256']
    original=(old/'capture_blender_normals.py').read_text();current=(HERE/'capture_blender_normals.py').read_text()
    def functions(text):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(text).body if isinstance(n,ast.FunctionDef)}
    before=functions(original);after=functions(current)
    assert all(after[name]==body for name,body in before.items()) and len(before)==6
    main_body=original[original.index('def main():'):original.index('\n\nif __name__ == "__main__":')]
    assert current.count(main_body)==1 and hashlib.sha256(main_body.encode()).hexdigest()==derive['original_main_sha256']
    for row in derive['copied_core']:assert (HERE/row['path']).read_bytes()==(old/row['path']).read_bytes()
    assert sha(HERE/'capture_blender_normals.py')==derive['capture_sha256']
    for p in HERE.glob('*.py'):ast.parse(p.read_text())
    print(json.dumps({'passed':True,'indexed_files':len(rows),'original_capture_functions_exact':6,'exact_core_aliases':5,
        'runtime_API_or_product_test_executed':False,'index_sha256':sha(HERE/'INDEX.json')}))
if __name__=='__main__':main()
