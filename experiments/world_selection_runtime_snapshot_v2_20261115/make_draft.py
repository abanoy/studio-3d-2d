"""Prepare source-only runtime snapshot draft; never apply product changes."""
from pathlib import Path
import ast
import hashlib
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

HELPERS = r'''
# Opt-in automated runtime snapshots exclude accumulated research evidence.
# The interactive owner builder retains its original full-source default.
RUNTIME_TREES = frozenset({'src','tests','tools','data','examples'})
RUNTIME_ROOTS = frozenset({'main.tscn','project.godot','run.py','launch.pyw'})
RUNTIME_NOTICES = frozenset({'THIRD_PARTY_NOTICES.md','docs/licenses.md'})
RUNTIME_OPTIONAL_ROOTS = RUNTIME_NOTICES | {'dependencies.json'}
RESOURCE_LITERAL = re.compile(rb"[\"']res://([^\"'\r\n\x00]*)[\"']")


def _read_blob_batch(root, entries):
    """Fetch only requested immutable blobs; never substitute working files."""
    if not entries:return {}
    batch=subprocess.check_output(['git','cat-file','--batch'],input=b''.join(oid+b'\n' for _,oid in entries),cwd=root)
    result={};offset=0
    for name,oid in entries:
        line_end=batch.index(b'\n',offset);actual,kind,size=batch[offset:line_end].split()
        assert actual==oid and kind==b'blob','Unexpected Git blob response'
        start=line_end+1;end=start+int(size);data=batch[start:end]
        assert len(data)==int(size) and batch[end:end+1]==b'\n','Truncated Git blob response'
        offset=end+1;result[name]=data
    assert offset==len(batch),'Unexpected trailing Git output'
    return result


def _runtime_entries(root, entries, revision):
    """Retain five runtime trees, entrypoints and their literal resource closure.

    Existing quoted res:// file references retain exact names and bytes; quoted
    directory references retain all existing files below that directory. Empty
    res://, missing/format-placeholder paths and excluded output/cache paths add
    nothing. A reference cannot introduce any path absent from the original
    validated Git candidate catalogue. Closure repeats for added resources.
    Relative Python modules and dynamic runtime fixtures remain available through
    the complete tools/tests/data/examples trees, rather than preload guessing.
    """
    by_name=dict(entries)
    assert RUNTIME_ROOTS <= by_name.keys(),'Missing runtime application entry points'
    selected={name for name in by_name if name.split('/',1)[0] in RUNTIME_TREES or name in RUNTIME_ROOTS or name in RUNTIME_OPTIONAL_ROOTS}
    prefixes={}
    for name in by_name:
        parts=name.split('/')
        for end in range(1,len(parts)):
            prefixes.setdefault('/'.join(parts[:end]),set()).add(name)
    cached={}
    while selected-cached.keys():
        pending=[(name,by_name[name]) for name in sorted(selected-cached.keys())]
        data=({name:(root/name).read_bytes() for name,_ in pending} if revision is None else _read_blob_batch(root,pending))
        cached.update(data)
        for body in data.values():
            for match in RESOURCE_LITERAL.finditer(body):
                try:reference=match.group(1).decode('utf-8').rstrip('/')
                except UnicodeDecodeError:continue
                if not reference:continue
                if reference in by_name:selected.add(reference)
                selected.update(prefixes.get(reference,()))
    return [(name,by_name[name]) for name in sorted(selected)],cached

'''


def sha(body):
    return hashlib.sha256(body).hexdigest()


def main():
    originals = {
        name: (ROOT/name).read_bytes() for name in (
            'tools/build_owner_review_snapshot.py',
            'tests/verify_world_selection_teardown.py',
            'tests/test_owner_review_snapshot.py',
            'tests/world_selection_teardown.gd',
            'tests/verify.py',
        )
    }
    builder = originals['tools/build_owner_review_snapshot.py'].decode().replace('\r\n','\n')
    builder = builder.replace('import argparse,hashlib,importlib.util,json,os,subprocess,sys,time',
                              'import argparse,hashlib,importlib.util,json,os,re,subprocess,sys,time', 1)
    builder = builder.replace('def safe_destination(target,name):', 'def validate_name(name):', 1)
    builder = builder.replace('    destination=target.joinpath(*parts)', '    return parts\n\n\ndef safe_destination(target,name):\n    parts=validate_name(name)\n    destination=target.joinpath(*parts)', 1)
    builder = builder.replace('def freeze_source(root,target,revision=None):', HELPERS + '\ndef freeze_source(root,target,revision=None,*,runtime_scope=False):', 1)
    builder = builder.replace("    assert not target.exists(),'Studio must not exist'", "    assert type(runtime_scope) is bool,'runtime_scope must be an explicit bool'\n    assert not target.exists(),'Studio must not exist'", 1)
    old_destinations = "    destinations={name:safe_destination(target,name) for name,_ in entries}\n    assert len({name.casefold() for name in destinations})==len(destinations),'Case-colliding snapshot paths'"
    new_destinations = "    cached=None\n    if runtime_scope:\n        # Validate the whole candidate catalogue before reading any source.\n        for name,_ in entries:validate_name(name)\n        assert len({name.casefold() for name,_ in entries})==len(entries),'Case-colliding snapshot paths'\n        entries,cached=_runtime_entries(root,entries,revision)\n    destinations={name:safe_destination(target,name) for name,_ in entries}\n    assert len({name.casefold() for name in destinations})==len(destinations),'Case-colliding snapshot paths'"
    assert old_destinations in builder
    builder = builder.replace(old_destinations,new_destinations,1)
    builder = builder.replace('    if revision is not None:\n        batch=subprocess.check_output(', '    if revision is not None and cached is None:\n        batch=subprocess.check_output(', 1)
    builder = builder.replace('        if batch is None:data=(root/name).read_bytes()', '        if cached is not None:data=cached[name]\n        elif batch is None:data=(root/name).read_bytes()', 1)
    driver = originals['tests/verify_world_selection_teardown.py'].decode().replace('\r\n','\n')
    driver = driver.replace('freeze_source(ROOT, project, revision)', 'freeze_source(ROOT, project, revision, runtime_scope=True)', 1)
    driver = driver.replace('"folder": str(folder), "profile": profile, "selected_cases": selected,', '"snapshot_scope": "runtime_dependency_closure",\n             "folder": str(folder), "profile": profile, "selected_cases": selected,', 1)
    tests = originals['tests/test_owner_review_snapshot.py'].decode().replace('\r\n','\n')
    snippet = (HERE/'runtime_tests_snippet.py').read_text(encoding='utf-8')
    tests = tests.replace("if __name__=='__main__':unittest.main()", snippet + "\n\nif __name__=='__main__':unittest.main()", 1)
    draft = HERE/'draft'
    draft_files = {
        'tools/build_owner_review_snapshot.py': builder,
        'tests/verify_world_selection_teardown.py': driver,
        'tests/test_owner_review_snapshot.py': tests,
    }
    for name, text in draft_files.items():
        ast.parse(text, filename=name)
        destination = draft/name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(text, encoding='utf-8', newline='\n')
    provenance = {
        'format': 'runtime_snapshot_source_draft_1',
        'status': 'SOURCE_ONLY_UNAPPLIED_NO_ENGINE_OR_GIT_EXECUTION',
        'original_sha256': {name: sha(body) for name,body in originals.items()},
        'draft_sha256': {name: sha((draft/name).read_bytes()) for name in draft_files},
        'unchanged_timeout_seconds': {'outer_verify': 180, 'normal_startup': 60, 'teardown': 110},
        'unchanged_gdscript_checks': 28,
    }
    (HERE/'SOURCE_PROVENANCE.json').write_text(json.dumps(provenance, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(provenance, indent=2))


if __name__=='__main__':main()
