"""Native body-to-dress following, real UI visibility and packed cold replay."""
from pathlib import Path
import argparse,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from run import command

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native-snapshot',type=Path,required=True)
    parser.add_argument('--classic',action='store_true')
    parser.add_argument('--output',type=Path)
    options=parser.parse_args()
    if os.name!='nt':parser.error('Private Windows desktop required')
    folder=(options.output or ROOT/'output'/('part-follow-gui-'+str(time.time_ns()))).resolve()
    assert folder.is_relative_to(ROOT/'output') and not folder.exists()
    folder.mkdir(parents=True);data=folder/'Data';data.mkdir()
    result={'status':'RUNNING','cases':{}}
    try:
        for label,marker,count in [('writer','CHARACTER_PARTS_FOLLOW_GUI ',14),('reader','CHARACTER_PARTS_FOLLOW_GUI_READ ',7)]:
            env=os.environ.copy()
            for key,leaf in [('APPDATA','Roaming'),('LOCALAPPDATA','Local')]:
                profile=folder/'User'/label/leaf;profile.mkdir(parents=True);env[key]=str(profile)
            extra=['--log-file',str(folder/(label+'-engine.log')),'--',str(options.native_snapshot.resolve(strict=True)),str(data)]
            if label=='reader':extra.append('--read')
            if options.classic:extra.append('--classic')
            args=command('tests/character_parts_follow_gui.gd',extra=extra)
            process=subprocess.run(args,cwd=ROOT,env=env,capture_output=True,timeout=230,creationflags=subprocess.CREATE_NO_WINDOW)
            (folder/(label+'-launcher.log')).write_bytes(process.stdout+process.stderr)
            engine=folder/(label+'-engine.log')
            text=engine.read_text(encoding='utf-8',errors='replace') if engine.exists() else ''
            receipt_path=Path(args[args.index('--receipt')+1])
            receipt=json.loads(receipt_path.read_bytes()) if receipt_path.exists() else {}
            result['cases'][label]={'exit':process.returncode,'private_receipt':receipt}
            assert process.returncode==0 and engine.exists(),text or (process.stdout+process.stderr).decode('utf-8','replace') or 'Private desktop launch ended before an engine log was created.'
            assert receipt['exit']==0 and receipt['child_desktop_confirmed'] and receipt['private_window_seen']
            assert not receipt['foreground_child_observed'] and not receipt['desktop_switch_requested'] and receipt['job_closed'] and receipt['desktop_closed']
            assert not any(error in text for error in ['SCRIPT ERROR','SHADER ERROR','ERROR:','FAIL ','ObjectDB instances leaked']),text
            lines=[line for line in text.splitlines() if line.startswith(marker)];assert len(lines)==1,text
            report=json.loads(lines[0][len(marker):]);assert report['checks']==count and report['failures']==0,report
            result['cases'][label]['report']=report
            print(label,count,'passed',flush=True)
        result['status']='PASS'
    except BaseException as error:
        result['status']='FAIL';result['error']=str(error);raise
    finally:
        (folder/'verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
        print(str(folder),flush=True)

if __name__=='__main__':main()
