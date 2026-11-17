"""Create an isolated Python reader successor; no application writes or imports."""
from pathlib import Path
import ast
import difflib
import hashlib
import json
import re

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def digest(raw):return hashlib.sha256(raw).hexdigest()


def main():
    path=ROOT/'tools/has_project.py';raw=path.read_bytes();source=raw.decode('utf-8')
    tree=ast.parse(source)
    eol='\r\n'if b'\r\n'in raw else'\n'
    member=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='members')
    calls=[n for n in ast.walk(member)if isinstance(n,ast.Call)and isinstance(n.func,ast.Name)and n.func.id=='members']
    assert len(calls)==4
    lines=source.splitlines(keepends=True)
    original=''.join(lines[member.lineno-1:member.end_lineno])
    private,count=re.subn(r'\bmembers\(', '_members_without_import_basis(', original)
    assert count==5
    wrapper='\n\ndef members(manifest,extended_ok=False):\n    return ImportBasis.members_with_capability(manifest,lambda view:_members_without_import_basis(view,extended_ok))\n'.replace('\n',eol)
    imports='try:from . import import_basis as ImportBasis\nexcept ImportError:import import_basis as ImportBasis\n'.replace('\n',eol)
    assert source.count(original)==1
    candidate=source.replace(original,private+wrapper,1)
    anchor='MAX_TOTAL = 512 * 1024 * 1024'+eol
    assert candidate.count(anchor)==1
    candidate=candidate.replace(anchor,imports+eol+anchor,1)
    restored=candidate.replace(imports+eol,'',1).replace(private+wrapper,original,1)
    assert restored==source
    proposed=HERE/'draft/tools/has_project.py';proposed.parent.mkdir(parents=True,exist_ok=True)
    assert not proposed.exists();proposed.write_bytes(candidate.encode('utf-8'))
    basis=HERE/'draft/tools/import_basis.py'
    assert not basis.exists();basis.write_bytes((HERE/'import_basis_candidate.py').read_bytes())
    ast.parse(candidate)
    patch=''.join(difflib.unified_diff(source.splitlines(True),candidate.splitlines(True),
        fromfile='original/tools/has_project.py',tofile='draft/tools/has_project.py'))
    (HERE/'has_project_reader.patch').write_text(patch,encoding='utf-8',newline='\n')
    report={'format':'has_basis_python_reader_draft_source_1','status':'ISOLATED_CPU_CANDIDATE_NOT_INSTALLED',
        'original':{'path':'tools/has_project.py','bytes':len(raw),'sha256':digest(raw)},
        'draft':{'path':'draft/tools/has_project.py','bytes':len(candidate.encode()),'sha256':digest(candidate.encode())},
        'basis_draft_sha256':digest(basis.read_bytes()),'renamed_recursive_calls':4,
        'new_facade_delegates_complete_old_body':True,'inverse_recipe_restores_all_original_bytes':True,
        'existing_budgets_asset_paths_cancel_archive_unpack_pack_logic_unchanged':True,
        'unmodified_original_source_still_exact':path.read_bytes()==raw}
    (HERE/'READER_DRAFT_SOURCE.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report))


if __name__=='__main__':main()
