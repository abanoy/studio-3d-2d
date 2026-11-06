"""Adaptive reader domain/independent PNG corpus; optional original measurement fixtures."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tests'))
from run import command
from png_reader_fixtures import make_fixtures

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path);parser.add_argument('--benchmark',choices=['sparse','noise','repeated','all']);options=parser.parse_args()
    folder=(options.output or ROOT/'output/cel-raster-adaptive'/str(time.time_ns())).resolve();folder.mkdir(parents=True,exist_ok=False)
    flags=dict(creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
    domain=subprocess.run([sys.executable,str(ROOT/'tests/verify_cel_raster_snapshot.py'),'--output',str(folder/'domain')],cwd=ROOT,capture_output=True,text=True,timeout=90,**flags)
    (folder/'domain.log').write_text(domain.stdout+domain.stderr,encoding='utf-8');assert domain.returncode==0,domain.stdout+domain.stderr
    reports={}
    def run(script,label,target,marker,extra=()):
        args=command(script,headless=True,extra=['--log-file',str(folder/(label+'-engine.log')),'--',str(target),*extra]);p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=240,**flags);log=p.stdout+p.stderr;(folder/(label+'.log')).write_text(log,encoding='utf-8')
        assert p.returncode==0 and marker in log and not any(s in log for s in ['ERROR:','FAIL ','ObjectDB instances leaked']),log
        result=json.loads(next(s[len(marker):] for s in log.splitlines() if s.startswith(marker)));assert result.get('failures',0)==0 and result.get('ok',True);reports[label]=result
    corpus=folder/'png-corpus';make_fixtures(corpus)
    for label,extra in [('png-eager',[]),('png-adaptive',['--adaptive'])]:run('tests/png_reader_compatibility.gd',label,corpus,'PNG_READER_COMPATIBILITY ',extra)
    for kind in ['sparse','noise','repeated']:
        if options.benchmark in [kind,'all']:
            target=folder/kind;target.mkdir();run('tests/cel_raster_adaptive_benchmark.gd',kind,target,'CEL_RASTER_ADAPTIVE_BENCHMARK ',['--noise'] if kind=='noise' else ['--repeat'] if kind=='repeated' else [])
    sources=['src/cel_raster_reader.gd','src/storage.gd','src/app.gd','tests/cel_raster_adaptive_unit.gd','tests/cel_raster_adaptive_benchmark.gd','tests/png_reader_compatibility.gd']
    proof=dict(scope='Explicit opt-in adaptive loader; production default remains eager. Headless validation/measurements, not app startup/native/device acceptance.',domain=json.loads((folder/'domain/verification.json').read_bytes()),reports=reports,source_sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in sources})
    (folder/'verification.json').write_text(json.dumps(proof,indent=2),encoding='utf-8');print(json.dumps(proof,indent=2))

if __name__=='__main__':main()
