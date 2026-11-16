"""CPU-only mocked tests, source diff and existing-catalogue dependency audit."""
from pathlib import Path
import ast
import difflib
import hashlib
import importlib.util
import io
import json
import sys
import unittest

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
DRAFT=HERE/'draft'


def sha(body):return hashlib.sha256(body).hexdigest()


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    provenance=json.loads((HERE/'SOURCE_PROVENANCE.json').read_bytes())
    source_unchanged={name:sha((ROOT/name).read_bytes())==digest for name,digest in provenance['original_sha256'].items()}
    assert all(source_unchanged.values()),source_unchanged
    sys.path.insert(0,str(DRAFT))
    tests=load('runtime_scope_draft_tests',DRAFT/'tests/test_owner_review_snapshot.py')
    stream=io.StringIO()
    result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(tests.RuntimeScopeTests))
    (HERE/'CPU_TESTS.log').write_text(stream.getvalue(),encoding='utf-8')
    assert result.wasSuccessful(),stream.getvalue()
    builder=load('runtime_scope_draft_builder',DRAFT/'tools/build_owner_review_snapshot.py')
    oldproof=ROOT/'output/world-selection-teardown/1794796856711017300/provenance.json'
    catalogue=json.loads(oldproof.read_bytes())['baseline_source_sha256']
    entries=[(name,None) for name in sorted(catalogue)]
    # No Git subprocess, output staging, engine, parser or native process query.
    # Read public source candidates only; retain counts/names/hashes, no contents.
    selected,cached=builder._runtime_entries(ROOT,entries,None)
    selected_names={name for name,_ in selected}
    expected_seed={name for name in catalogue if name.split('/',1)[0] in builder.RUNTIME_TREES or name in builder.RUNTIME_ROOTS or name in builder.RUNTIME_NOTICES}
    external=sorted(selected_names-expected_seed)
    counts={}
    for name in selected_names:
        domain=name.split('/',1)[0];counts[domain]=counts.get(domain,0)+1
    audit={
        'format':'runtime_snapshot_draft_cpu_1',
        'status':'PASS_SOURCE_ONLY_UNAPPLIED',
        'mocked_tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
        'original_source_unchanged':source_unchanged,
        'existing_failed_snapshot_catalogue_sha256':sha(oldproof.read_bytes()),
        'old_catalogue_files':len(catalogue),'runtime_files':len(selected),
        'runtime_bytes':sum(len(body) for body in cached.values()),
        'runtime_counts_by_top_level':dict(sorted(counts.items())),
        'external_literal_resource_dependency_names':external,
        'explicit_support_notices':sorted(builder.RUNTIME_NOTICES & selected_names),
        'excluded_unreferenced_experiment_files':sum(name.startswith('experiments/') and name not in selected_names for name in catalogue),
        'excluded_unreferenced_document_files':sum(name.startswith('docs/') and name not in selected_names for name in catalogue),
        'source_semantics':'Current old-snapshot candidate names; current unchanged working source bytes. This audit does not represent a fresh Git inventory or actual scoped runtime.',
        'limitations':['No engine/parser execution; no new full or teardown PASS.','Shared old-revision test overlay remains current tests/world_selection_teardown.gd after baseline snapshot.','Dynamic resource paths outside the five retained trees require a quoted existing directory/file dependency or an explicit reviewed runtime support seed.'],
    }
    diffs=[]
    for name,digest in provenance['draft_sha256'].items():
        body=(DRAFT/name).read_bytes();assert sha(body)==digest
        ast.parse(body,filename=name)
        diffs.extend(difflib.unified_diff((ROOT/name).read_text(encoding='utf-8').splitlines(keepends=True),body.decode().splitlines(keepends=True),fromfile='a/'+name,tofile='b/'+name))
    (HERE/'REVIEW.diff').write_text(''.join(diffs),encoding='utf-8',newline='\n')
    (HERE/'CPU_RESULT.json').write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(audit,indent=2))


if __name__=='__main__':main()
