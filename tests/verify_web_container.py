"""Browser HAS adapter against real native packages and the independent desktop codec."""
from pathlib import Path
import argparse,hashlib,json,struct,subprocess,sys,time,zipfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools'))
from run import command
import has_project

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--native-project',type=Path,action='append',default=[]);options=parser.parse_args()
    folder=ROOT/'output/web-container'/str(time.time_ns());folder.mkdir(parents=True)
    inputs=[ROOT/'examples/tutorials/first-movie.has',ROOT/'examples/tutorials/practice.has',*options.native_project]
    originals={str(p):hashlib.sha256(p.read_bytes()).hexdigest()for p in inputs};plan={'inputs':[str(p.resolve())for p in inputs],'bad':[]}
    with zipfile.ZipFile(inputs[0])as archive:original={name:archive.read(name)for name in archive.namelist()}
    def case(name,change):
        files=original.copy();change(files);target=folder/(name+'.has')
        with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED)as archive:
            for key,data in files.items():archive.writestr(key,data)
        plan['bad'].append(str(target))
    case('traversal',lambda f:f.update({'../escape.txt':b'x'}))
    case('stream',lambda f:f.update({'assets/foo:stream':b'x'}))
    case('device',lambda f:f.update({'assets/CON.glb':b'x'}))
    case('unexpected',lambda f:f.update({'surprise.gd':b'never executed'}))
    case('directory',lambda f:f.update({'assets/':b''}))
    case('checksum',lambda f:f.update({'project.json':f['project.json']+b' '}))
    case('bad-json',lambda f:f.update({'has.json':b'{broken'}))
    for label,value in [('wrong-version',99),('bool-version',True)]:case(label,lambda f,v=value:f.update({'has.json':json.dumps({**json.loads(f['has.json']),'version':v}).encode()}))
    case('bool-schema',lambda f:f.update({'project.json':json.dumps({**json.loads(f['project.json']),'schema_version':True}).encode()}))
    case('bool-format',lambda f:f.update({'has.json':json.dumps({**json.loads(f['has.json']),'format':False}).encode()}))
    case('linked',lambda f:f.update({'has.json':json.dumps({**json.loads(f['has.json']),'storage':'linked'}).encode()}))
    case('duplicate-inventory',lambda f:f.update({'has.json':json.dumps({**json.loads(f['has.json']),'payload':json.loads(f['has.json'])['payload']*2}).encode()}))
    raw=bytearray(inputs[0].read_bytes());central=raw.index(b'PK\x01\x02');struct.pack_into('<I',raw,central+24,129*1024*1024)
    for name,data in [('oversized',raw),('truncated',inputs[0].read_bytes()[:-11]),('not-zip',b'not a zip')]:
        target=folder/(name+'.has');target.write_bytes(data);plan['bad'].append(str(target))
    (folder/'plan.json').write_text(json.dumps(plan,ensure_ascii=False),encoding='utf-8')
    process=subprocess.run(command('tests/web_container_unit.gd',headless=True,extra=['--',str(folder)]),cwd=ROOT,capture_output=True,encoding='utf-8',errors='replace',timeout=120)
    log=process.stdout+process.stderr;(folder/'engine.log').write_text(log,encoding='utf-8')
    assert process.returncode==0 and 'WEB_HAS_CONTAINER 'in log and not any(v in log for v in ['ERROR:','FAIL ','ObjectDB instances leaked']),log
    result=json.loads((folder/'result.json').read_text());assert result['failures']==0 and len(result['repacked'])==len(inputs)
    for i,source in enumerate(result['repacked']):
        decoded=has_project.unpack({'path':source,'folder':str(folder/('python-'+str(i)))})
        assert decoded['ok']and (Path(decoded['folder'])/'project.json').read_bytes()==(folder/('unpack-'+str(i))/'project.json').read_bytes()
    for name,digest in originals.items():assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==digest
    result.update(folder=str(folder),original_python_readers=len(inputs),native_projects=[str(p)for p in options.native_project],browser_runtime_tested=False)
    (ROOT/'output/web-container-verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))

if __name__=='__main__':main()
