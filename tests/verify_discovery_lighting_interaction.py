"""Focused Discover/import, authored lighting, Undo and packed cold replay."""
from pathlib import Path
import argparse,json,os,re,subprocess,sys,time
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'tests'))
from run import command
from verify_character_parts import windows_case


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--graphical',action='store_true')
    options=parser.parse_args()
    if os.name!='nt':parser.error('Owned Windows test launcher required')
    output=ROOT/'output'/('discovery-lighting-interaction-'+str(time.time_ns()))
    output.mkdir(parents=True)
    result={'status':'FAIL','checks':0,'graphical':options.graphical,'cases':[]}
    try:
        for theme in ('neon','classic'):
            data=output/theme;data.mkdir()
            for phase,count in (('writer',16),('reader',7)):
                case=data/phase;case.mkdir();env=dict(os.environ)
                env.update(PYTHONDONTWRITEBYTECODE='1',HYBRID_PYTHON=sys.executable)
                for name,leaf in (('APPDATA','Roaming'),('LOCALAPPDATA','Local')):
                    path=case/leaf;path.mkdir();env[name]=str(path)
                extra=['--audio-driver','Dummy','--log-file',str(case/'engine.log'),'--',str(data)]
                if phase=='reader':extra.append('--read')
                if theme=='classic':extra.append('--classic')
                args=command('tests/discovery_lighting_interaction.gd',headless=not options.graphical,extra=extra)
                row={'theme':theme,'phase':phase,'status':'FAIL'};result['cases'].append(row)
                if options.graphical:
                    child=subprocess.run(args,cwd=ROOT,env=env,capture_output=True,timeout=180,creationflags=subprocess.CREATE_NO_WINDOW)
                    (case/'launcher.log').write_bytes(child.stdout+child.stderr);code=child.returncode
                    receipt=Path(args[args.index('--receipt')+1]);proof=json.loads(receipt.read_bytes()) if receipt.is_file() else {}
                    row['ownership']=proof
                    assert proof.get('exit')==0 and proof.get('child_desktop_confirmed') and proof.get('private_window_seen')
                    assert proof.get('job_closed') and proof.get('desktop_closed') and not proof.get('foreground_child_observed') and not proof.get('desktop_switch_requested'),proof
                else:
                    code=windows_case(args,case,env);proof=json.loads((case/'ownership.json').read_bytes());row['ownership']=proof
                    assert all(proof.get(k) is True for k in ('wrapper_reaped','active_zero','job_closed')),proof
                text=(case/'engine.log').read_text(encoding='utf-8',errors='replace')
                marker='DISCOVERY_LIGHTING_READ ' if phase=='reader' else 'DISCOVERY_LIGHTING_WRITE '
                reports=[json.loads(line[len(marker):]) for line in text.splitlines() if line.startswith(marker)]
                assert code==0 and not re.search(r'SCRIPT ERROR|SHADER ERROR|^ERROR:|^FAIL |ObjectDB instances leaked',text,re.M),text
                assert len(reports)==1 and reports[0]['checks']==count and reports[0]['failures']==0 and reports[0]['graphics']==options.graphical,reports
                assert len(re.findall(r'^PASS ',text,re.M))==count,text
                row.update(status='PASS',report=reports[0]);result['checks']+=count
                print(theme,phase,count,'passed',flush=True)
        assert result['checks']==46
        result['status']='PASS'
    except BaseException as error:
        result['error']=str(error);raise
    finally:
        (output/'verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
        print(str(output),flush=True)


if __name__=='__main__':main()
