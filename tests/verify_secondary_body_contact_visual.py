"""Private ordinary-Open Miku contact and actual skinned-surface measurement."""
from pathlib import Path
import argparse,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from run import command

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project',type=Path,required=True)
    parser.add_argument('--collider-input',type=Path,required=True)
    parser.add_argument('--alignment',type=Path,required=True)
    parser.add_argument('--output',type=Path)
    options=parser.parse_args()
    if os.name!='nt':parser.error('This check requires the private Windows desktop launcher')
    folder=(options.output or ROOT/'output'/('secondary-contact-visual-'+str(time.time_ns()))).resolve()
    assert folder.is_relative_to(ROOT/'output') and not folder.exists()
    folder.mkdir(parents=True);data=folder/'Data';data.mkdir()
    env=os.environ.copy()
    for key,leaf in [('APPDATA','Roaming'),('LOCALAPPDATA','Local')]:
        path=folder/'User'/leaf;path.mkdir(parents=True);env[key]=str(path)
    args=command('tests/secondary_body_contact_visual.gd',extra=['--log-file',str(folder/'engine.log'),'--',str(data),str(options.project.resolve(strict=True)),str(options.collider_input.resolve(strict=True)),str(options.alignment.resolve(strict=True))])
    process=subprocess.run(args,cwd=ROOT,env=env,capture_output=True,timeout=230,creationflags=subprocess.CREATE_NO_WINDOW)
    (folder/'launcher.log').write_bytes(process.stdout+process.stderr)
    receipt_path=Path(args[args.index('--receipt')+1])
    receipt=json.loads(receipt_path.read_bytes()) if receipt_path.exists() else {}
    engine=folder/'engine.log'
    text=engine.read_text(encoding='utf-8',errors='replace') if engine.exists() else ''
    result={'status':'FAIL','exit':process.returncode,'private_receipt':receipt}
    try:
        assert process.returncode==0 and engine.exists(),text or 'Private test launch ended before an engine log was created.'
        assert receipt['exit']==0 and receipt['child_desktop_confirmed'] and receipt['private_window_seen']
        assert not receipt['foreground_child_observed'] and not receipt['desktop_switch_requested']
        assert receipt['job_closed'] and receipt['desktop_closed']
        assert not any(error in text for error in ['SCRIPT ERROR','SHADER ERROR','ERROR:','FAIL ','ObjectDB instances leaked']),text
        marker='SECONDARY_BODY_CONTACT_VISUAL '
        lines=[line for line in text.splitlines() if line.startswith(marker)];assert len(lines)==1,text
        report=json.loads(lines[0][len(marker):]);assert report['checks']==15 and report['failures']==0,report
        assert report['readbacks_balanced'] and Path(report['user_profile']).resolve().is_relative_to(folder/'User')
        result.update(report=report,visual_review_required=True)
        # A successful runtime measurement alone did not prove the original fix:
        # its earlier15 controls passed while1059 actual skin pairs penetrated.
        assert report['skin_surface_capsule_clear'] is True and report['penetrating_skin_vertex_pairs']==0,report
        assert report['minimum_skin_clearance']>=-.00005 and 0<=report['maximum_palette_disagreement']<=.00001,report
        result.update(status='CLEAR_CAPSULE_CONTACT_VISUAL_REVIEW_PENDING',contact_requirement_passed=True)
    finally:
        (folder/'verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
        print(json.dumps({'folder':str(folder),**result},indent=2))

if __name__=='__main__':main()
