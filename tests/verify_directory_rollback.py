"""Bounded old-payload validation and real kill before replacement of a bad primary."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from run import command


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    folder=(args.output or ROOT/'output/directory-rollback'/str(time.time_ns())).resolve()
    folder.mkdir(parents=True,exist_ok=False)
    reports={}
    def execute(script,label,marker,extra,env=None):
        result=subprocess.run(command('tests/'+script+'.gd',headless=True,
                                      extra=['--log-file',str(folder/(label+'-engine.log')),'--',*map(str,extra)]),
                              cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=90,env=env)
        text=result.stdout+result.stderr;(folder/(label+'.log')).write_text(text,encoding='utf-8')
        assert result.returncode==0 and marker in text and not any(x in text for x in ['ERROR:','FAIL ','ObjectDB instances leaked']),text
        return json.loads(next(line[len(marker):] for line in text.splitlines() if line.startswith(marker)))
    unit=folder/'unit';unit.mkdir()
    reports['unit']=execute('directory_rollback_unit','unit','DIRECTORY_ROLLBACK_UNIT ',[unit])
    assert reports['unit']['failures']==0
    if os.name=='posix':
        case=folder/'interruption';case.mkdir()
        proof=execute('directory_rollback_prepare','prepare','DIRECTORY_ROLLBACK_PREPARED ',[case]);project=Path(proof['project'])
        shim=folder/'interrupted-python'
        shim.write_text('#!'+sys.executable+'\n'+
                        'import os,signal,sys\nfrom pathlib import Path\nfrom unittest import mock\n'+
                        'sys.path.insert(0,'+repr(str(ROOT))+')\n'+
                        'from tools import directory_commit as dc\n'+
                        'original=dc.os.replace\n'+
                        'def replace(source,target):\n if Path(target).name=="project.json":os.kill(os.getpid(),signal.SIGKILL)\n return original(source,target)\n'+
                        'sys.argv=sys.argv[1:]\n'+
                        'with mock.patch.object(dc.os,"replace",side_effect=replace):dc.main()\n',encoding='utf-8')
        shim.chmod(0o700)
        result=execute('directory_commit_smoke','interrupted','DIRECTORY_COMMIT_SMOKE ',
                       [project,2,case/'result.json','--inspect-backup'],dict(os.environ,HYBRID_PYTHON=str(shim)))
        assert 'status' in result['error'] and not result['load_error'] and result['frame']==0,result
        digest=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
        assert digest(project/'project.json')==proof['primary_sha256']
        assert digest(project/'project.backup.json')==proof['backup_sha256']
        assert digest(Path(proof['original']))==proof['original_sha256']
        pending=list(project.glob('project.json.*.tmp'));assert len(pending)==1
        assert json.loads(pending[0].read_bytes())['editor']['frame']==2
        reports['actual_interruption']=dict(result=result,worker_killed_before_primary_promotion=True,
                                            original_primary_and_good_backup_unchanged=True,
                                            good_backup_loaded_by_actual_godot=True,verified_candidate_retained=True,
                                            original_source_unchanged=True)
    else:
        reports['actual_interruption']={'skipped':'POSIX executable/SIGKILL fixture; native Windows gate remains'}
    result=dict(reports=reports,folder=str(folder),source_sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in
                ['src/storage.gd','src/project_payload_guard.gd','src/cel_png_verifier.gd','tests/directory_rollback_unit.gd',
                 'tests/directory_rollback_prepare.gd','tests/directory_commit_smoke.gd','tests/verify_directory_rollback.py']})
    (folder/'verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
