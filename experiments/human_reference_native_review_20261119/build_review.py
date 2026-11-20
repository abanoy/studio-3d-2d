"""Prepare a private native size-reference review; never launch an application.

This public recipe stores no model, screenshot or runtime snapshot. Callers must
provide an explicit committed revision and a fresh checkout/output destination.
"""
from pathlib import Path, PureWindowsPath
import argparse
import hashlib
import json
import os
import shutil
import stat
import sys
import time

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
RECIPE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from tools.build_owner_review_snapshot import freeze_source

SOURCE_SHA='3caa50b76d0f481bb7ee66daeb6ebe7485aefb966140321b599ca60d9d464b56'
PARAMETERS_SHA='0f8f746ca68a821acaf9e502b6895a2f2798d8d1d2bd62569d78deea652fc0ef'
RAW_SHA='f7b4573b241b3e91c7c5f58bed342133a4e5f7e0c1125e1cedc49723ace9b288'
PYTHON=Path(r'C:\Program Files\Python313\python.exe')
PYTHONW=Path(r'C:\Program Files\Python313\pythonw.exe')
GODOT=Path(r'C:\a\tools\Godot\Godot_v4.6-stable_win64.exe')
CODE_FILES=('native_reference.gd','owner_launch.pyw','verify_native_reference.py')

def identity(path):
    path=Path(path);before=path.stat()
    with path.open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
    after=path.stat()
    assert (before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns),'Input changed while hashing'
    return dict(sha256=digest,bytes=after.st_size,mtime_ns=after.st_mtime_ns)

def no_links(path):
    path=Path(path).absolute()
    assert '..' not in path.parts,'Lexical traversal refused'
    for part in (path,*path.parents):
        if part.exists():
            info=part.lstat()
            assert not stat.S_ISLNK(info.st_mode) and not getattr(info,'st_file_attributes',0)&0x400,'Linked/reparse path refused: '+str(part)
    return path

def descendant(base,name):
    assert isinstance(name,str) and name and not PureWindowsPath(name).drive and not Path(name).is_absolute(),'Relative fixture member required'
    path=no_links(base/name)
    assert path.resolve(strict=True).is_relative_to(base.resolve(strict=True)) and path.is_file(),'Fixture member escapes its root'
    return path

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--revision',required=True,help='Explicit committed revision; HEAD is never chosen implicitly')
    parser.add_argument('--output',required=True,type=Path,help='Fresh destination under this checkout/output')
    parser.add_argument('--fixture-root',type=Path,default=os.environ.get('HYBRID_NATIVE_FIXTURES'),help='Prepared fixture root containing wind-review-inputs.json; may use explicit HYBRID_NATIVE_FIXTURES')
    options=parser.parse_args()
    assert options.fixture_root is not None,'Select an explicit prepared fixture root'
    output=no_links(options.output)
    boundary=(ROOT/'output').resolve()
    assert output.resolve().is_relative_to(boundary) and output.resolve()!=boundary and not output.exists(),'Fresh checkout/output descendant required'
    fixture_root=no_links(options.fixture_root).resolve(strict=True)
    manifest=descendant(fixture_root,'wind-review-inputs.json')
    assert manifest.stat().st_size<=1024*1024,'Fixture metadata exceeds 1 MiB'
    document=json.loads(manifest.read_bytes())
    assert document.get('format')=='has_wind_review_inputs_1' and isinstance(document.get('inputs'),dict),'Wrong fixture metadata format'
    role=document['inputs'].get('vrm0');assert isinstance(role,dict),'VRM0 role is missing'
    source=descendant(fixture_root,role['source']);parameters=descendant(fixture_root,role['parameters'])
    originals={str(path):identity(path) for path in (manifest,source,parameters)}
    assert originals[str(source)]['sha256']==SOURCE_SHA and originals[str(parameters)]['sha256']==PARAMETERS_SHA,'Pinned VRM0 source/report checksum differs'
    report=json.loads(parameters.read_bytes())
    assert report.get('kind')=='vrm_preparation' and report.get('vrm_version')=='0.x' and report.get('scale')==1.0 and report.get('source_sha256')==RAW_SHA,'Original VRM0 provenance differs'
    assert all(path.is_file() for path in (PYTHON,PYTHONW,GODOT)),'Reviewed runtime executable paths are missing'
    output.mkdir(parents=True,exist_ok=False)
    studio=output/'Studio'
    commit,source_hashes=freeze_source(ROOT,studio,options.revision,runtime_scope=True)
    inputs=studio/'review-input/vrm0';inputs.mkdir(parents=True)
    for path,name in ((source,'scene.glb'),(parameters,'parameters.json')):
        shutil.copy2(path,inputs/name)
        assert identity(inputs/name)==originals[str(path)],'Staged bytes or modification time differ'
    assert all(identity(path)==value for path,value in originals.items()),'Original fixture input changed'
    review=studio/'review';review.mkdir()
    for name in CODE_FILES:shutil.copyfile(RECIPE/name,review/name)
    profile='HAS Native Human Reference '+str(time.time_ns())
    (studio/'override.cfg').write_text('[application]\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir_name='+json.dumps(profile)+'\n',encoding='utf-8')
    (studio/'output').mkdir()
    launcher='@echo off\r\nsetlocal\r\nstart "" "'+str(PYTHONW)+'" "%~dp0Studio\\review\\owner_launch.pyw"\r\n'
    (output/'Open six-foot VRM review.bat').write_bytes(launcher.encode('utf-8'))
    notes='''# Private six-foot VRM review

Prepared only; no application or verification was launched by the builder.

Open **Open six-foot VRM review.bat** when ready. The separate Studio profile
opens an empty scene, uses the ordinary height review, explicitly selects the
six-foot Scale 1 reference and displays its Simple size controls. It leaves
the app open. Its screenshot and compact result stay under Studio/output.

This is an existing prepared VRM0 size workflow, not native fidelity
certification or owner acceptance. Do not publish this private model or art.

The coordinator may run Studio/review/verify_native_reference.py with
--lease-confirmed after the graphics lane closes. Add --body-guard for a
guarded revision: expect 25 checks rather than the original 23. The additional
checks require a clear refusal of unsupported Body Physics and unchanged
model/pose/reference/topology. This is not scale-preserving body simulation.
'''
    (output/'PRIVATE_REVIEW.md').write_text(notes,encoding='utf-8')
    artifacts=[output/'PRIVATE_REVIEW.md',output/'Open six-foot VRM review.bat',studio/'override.cfg',*[review/name for name in CODE_FILES]]
    preparation=dict(format='has_native_human_reference_review_1',status='PREPARED_UNRUN',source_commit=commit,requested_revision=options.revision,runtime_scope=True,source_hashes=source_hashes,profile=profile,original_inputs=originals,staged_inputs={str((inputs/name).relative_to(studio)):identity(inputs/name) for name in ('scene.glb','parameters.json')},python=str(PYTHON),pythonw=str(PYTHONW),godot=str(GODOT),review_artifact_hashes={str(path.relative_to(output)):identity(path)['sha256'] for path in artifacts},scope='Existing prepared VRM0 size-reference workflow only; not native fidelity certification. No automated or owner launch performed.')
    (output/'preparation.json').write_text(json.dumps(preparation,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(folder=str(output),source_commit=commit,runtime_files=len(source_hashes),copied_input_files=2,copied_input_bytes=sum(row['bytes'] for row in preparation['staged_inputs'].values()),status='PREPARED_UNRUN'),indent=2))

if __name__=='__main__':main()
