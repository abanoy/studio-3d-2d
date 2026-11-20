"""Manual owner entry only. Nothing starts merely by preparing this file."""
from pathlib import Path
import ctypes
import hashlib
import json
import os
import subprocess
import time
import traceback

ROOT=Path(__file__).resolve().parents[1]
PYTHON=Path(r'C:\Program Files\Python313\python.exe')
GODOT=Path(r'C:\a\tools\Godot\Godot_v4.6-stable_win64.exe')

def no_reparse(path):
    path=Path(path).absolute()
    assert '..' not in path.parts,'Lexical traversal refused'
    for part in (path,*path.parents):
        if part.exists():
            assert not part.is_symlink() and not getattr(part.lstat(),'st_file_attributes',0)&0x400,'Linked/reparse launch path refused'
    return path

def review_artifacts(preparation):
    expected={'PRIVATE_REVIEW.md','Open six-foot VRM review.bat','Studio/override.cfg',*['Studio/review/'+name for name in ('native_reference.gd','owner_launch.pyw','verify_native_reference.py')]}
    records=preparation['review_artifact_hashes'];normalized={name.replace('\\','/'):digest for name,digest in records.items()}
    assert len(normalized)==len(records) and set(normalized)==expected,'Unexpected review artifact membership'
    for name,digest in normalized.items():
        path=no_reparse(ROOT.parent.joinpath(*name.split('/')))
        assert path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest()==digest,'Prepared review artifact changed: '+name

try:
    assert (ROOT/'project.godot').is_file() and (ROOT.parent/'preparation.json').is_file(),'Use a prepared review snapshot, not the public recipe directory'
    no_reparse(ROOT.parent/'preparation.json')
    preparation=json.loads((ROOT.parent/'preparation.json').read_bytes());review_artifacts(preparation)
    inputs={name.replace('\\','/'):stamp for name,stamp in preparation['staged_inputs'].items()}
    assert len(inputs)==2 and set(inputs)=={'review-input/vrm0/scene.glb','review-input/vrm0/parameters.json'},'Unexpected prepared input membership'
    for name,stamp in inputs.items():
        path=no_reparse(ROOT.joinpath(*name.split('/')));info=path.stat()
        assert info.st_size==stamp['bytes'] and info.st_mtime_ns==stamp['mtime_ns'] and hashlib.sha256(path.read_bytes()).hexdigest()==stamp['sha256'],'Prepared input changed'
    assert PYTHON.is_file() and GODOT.is_file(),'Reviewed Python/Godot paths are missing'
    assert no_reparse(ROOT/'output').is_dir(),'Prepared review output is missing'
    folder=no_reparse(ROOT/'output'/('owner-native-reference-'+str(time.time_ns())))
    folder.mkdir(exist_ok=False);no_reparse(folder)
    (folder/'display.cfg').write_text('[display]\ntheme="neon"\npercent=100\n',encoding='utf-8')
    env=os.environ.copy();env['HYBRID_PYTHON']=str(PYTHON);env['HYBRID_GODOT']=str(GODOT);env['PYTHONDONTWRITEBYTECODE']='1'
    with (folder/'owner-launch.log').open('wb') as log:
        subprocess.Popen([str(GODOT),'--path',str(ROOT),'--log-file',str(folder/'engine.log'),'--script','res://review/native_reference.gd','--','--owner',str(folder)],cwd=ROOT,env=env,stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW)
except Exception:
    ctypes.windll.user32.MessageBoxW(None,traceback.format_exc(),'HAS native reference review could not start',0x10)
