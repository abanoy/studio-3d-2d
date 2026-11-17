"""Pin/copy sealed predecessor into a new corrected, fail-closed CPU draft."""
from pathlib import Path
import ast
import hashlib
import json

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
OLD=ROOT/'experiments/six_foot_import_basis_candidate_20261116'


def put(name,raw):
    p=HERE/name;p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb')as f:f.write(raw)


def once(text,old,new):
    assert text.count(old)==1,old
    return text.replace(old,new,1)


def main():
    original=(OLD/'import_basis_candidate.py').read_bytes()
    assert hashlib.sha256(original).hexdigest()=='8eaffa26073699f3d7b9b108c0570ab4f761a8dc3a33d0aae61d629d0d9352a3'
    source=original.decode()
    source=once(source,'from decimal import Decimal, localcontext',
        'from decimal import Decimal, localcontext, Context, ROUND_HALF_EVEN, InvalidOperation, DivisionByZero, Overflow')
    source=once(source,"TARGET = Decimal('1.8288')", "TARGET = Decimal('1.8288')\nFIXED_CONTEXT = Context(prec=50, rounding=ROUND_HALF_EVEN, Emin=-999999, Emax=999999, capitals=1, clamp=0, flags=[], traps=[InvalidOperation, DivisionByZero, Overflow])")
    source=once(source,'with localcontext() as context:\n        context.prec = 50', 'with localcontext(FIXED_CONTEXT):')
    source=once(source,"    require(type(model) is dict, 'Model dictionary required')", "    require(type(capability) is bool, 'Capability flag must be an actual boolean')\n    require(type(model) is dict, 'Model dictionary required')")
    source=once(source,"    require(type(model) is dict and type(assessment) is dict, 'Model and assessment required')", "    require(type(fresh_raw) is bool, 'Fresh raw flag must be an actual boolean')\n    require(type(model) is dict and type(assessment) is dict, 'Model and assessment required')")
    source=once(source,'def members_with_capability(document, legacy_members):', 'def members_with_capability(document, legacy_members, *, runtime_basis_ready=False):')
    source=once(source,'    inspect_capability(document)\n    return legacy_members(_legacy_validation_view(document))',
        "    require(type(runtime_basis_ready) is bool, 'Runtime readiness must be an actual internal boolean')\n    admission = inspect_capability(document)\n    require(not admission['basis_required'] or runtime_basis_ready, 'Active import basis is unavailable until the matching HAS runtime is qualified')\n    return legacy_members(_legacy_validation_view(document))")
    ast.parse(source)
    put('import_basis_v2.py',source.encode());put('draft/tools/import_basis.py',source.encode())
    put('draft/tools/has_project.py',(OLD/'draft/tools/has_project.py').read_bytes())
    test=(OLD/'test_import_basis_candidate.py').read_text()
    test=once(test,'import import_basis_candidate as B','import import_basis_v2 as B')
    test=test.replace('B.members_with_capability(wrapped,old.members)','B.members_with_capability(wrapped,old.members,runtime_basis_ready=True)')
    test=test.replace('B.members_with_capability(bad,old.members)','B.members_with_capability(bad,old.members,runtime_basis_ready=True)')
    test=once(test,"target=HERE/'CPU_RESULT_v2.json'", "target=HERE/'PYTHON_CPU_RESULT.json'")
    test=test.replace("'SYNTHETIC_CONTRACT_ONLY'","'SYNTHETIC_V2_CONTEXT_FIXED_AND_RUNTIME_CLOSED'")
    put('test_python_v2.py',test.encode())
    report={'format':'has_six_foot_v2_predecessor_1','original_packet_index_sha256':hashlib.sha256((OLD/'INDEX.json').read_bytes()).hexdigest(),
        'original_helper_sha256':hashlib.sha256(original).hexdigest(),'v2_helper_sha256':hashlib.sha256(source.encode()).hexdigest(),
        'bounded_corrections':['Fully explicit decimal context; nearest ties-to-even50 significant digits','Strict actual-boolean capability/fresh flags','Worker facade defaults to refusing active basis until internally qualified runtime readiness'],
        'original_sealed_packet_untouched':True,'main_files_modified':False}
    put('PREDECESSOR.json',(json.dumps(report,indent=2)+'\n').encode())
    print(json.dumps(report))


if __name__=='__main__':main()
