"""Verify schema4 storage/package foundation; UI multi-object editing is the next step."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools'))
from run import command
import has_project as has


def run(args,timeout=100):
    process=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=timeout)
    text=process.stdout+process.stderr
    if process.returncode or any(error in text for error in ('SCRIPT ERROR','SHADER ERROR','Shader compilation failed','FAIL ','ObjectDB instances leaked')):
        raise RuntimeError(text)
    return text


def read_package(expected,opened):
    text=run(command('tests/world_document_read.gd',False,['--',str(expected),str(opened)]))
    for line in text.splitlines():
        if line.startswith('WORLD_PACKAGE_READ '):return json.loads(line.removeprefix('WORLD_PACKAGE_READ '))
    raise RuntimeError('Missing package-read result\n'+text)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    print(run([sys.executable,'-m','unittest','discover','-s','tests','-p','test_has*.py']))
    text=run(command('tests/world_document_smoke.gd'))
    (ROOT/'output/world-document-verification.log').write_text(text,encoding='utf-8')
    if 'WORLD_DOCUMENT_SMOKE ' not in text or '"failures":0' not in text:raise RuntimeError(text)
    report=json.loads((ROOT/'output/world-document-result.json').read_text(encoding='utf-8'))
    folder=Path(report['folder']);snapshot=Path(report['snapshot'])
    request={'folder':str(snapshot),'path':str(folder/'multi-object.has'),'storage':'packed',
             'references':report['references'],'cache_root':str(folder/'cache')}
    has.pack(request)
    inputs=folder/'inputs';moved=folder/'moved-inputs'
    output=(ROOT/'output').resolve()
    assert inputs.resolve().is_relative_to(output) and moved.resolve().is_relative_to(output) and inputs.parent==moved.parent
    inputs.rename(moved)
    results={}
    try:
        opened=folder/'packed-open'
        has.unpack({'path':request['path'],'folder':str(opened)})
        results['packed']=read_package(snapshot,opened)
    finally:
        moved.rename(inputs)
    request['storage']='linked';request['path']=str(folder/'linked-world.has');has.pack(request)
    inputs.rename(moved)
    try:
        opened=folder/'linked-open';read={'path':request['path'],'folder':str(opened)}
        missing=has.unpack(read)
        assert not missing['ok'] and len(missing['missing'])==3
        relinks={name:str(moved/Path(reference).name) for name,reference in report['references'].items() if Path(reference).parent==inputs}
        result=has.unpack({**read,'relinks':relinks});assert result['ok']
        results['linked']=read_package(snapshot,opened)
        results['shared_asset_relinks']=len(missing['missing'])
    finally:
        moved.rename(inputs)
    for name,key in [('empty','empty_snapshot'),('native','native_snapshot')]:
        if not report[key]:continue
        source=Path(report[key]);target=folder/(name+'.has');opened=folder/(name+'-open')
        has.pack({'folder':str(source),'path':str(target),'storage':'packed','references':{},'cache_root':str(folder/'cache')})
        has.unpack({'path':str(target),'folder':str(opened)})
        results[name]=read_package(source,opened)
    for path,digest in report['originals'].items():assert has.sha(Path(path))==digest
    report['package_checks']=results;report['original_inputs_unchanged']=True
    (ROOT/'output/world-document-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({'checks':report['checks'],'failures':report['failures'],'native_projects':report['native_projects'],'packages':results,'folder':str(folder)},indent=2))


if __name__=='__main__':main()
