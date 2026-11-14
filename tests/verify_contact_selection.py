"""Native selection versus frozen source poses, with independent CPU-baked bounds."""
from pathlib import Path
import json,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command

def main():
    reference=json.loads((ROOT/'output/contact-persistence-verification.json').read_text())['writer']['packed']
    folder=ROOT/'output/contact-selection'/str(time.time_ns());folder.mkdir(parents=True)
    # Geometry and selection do not depend on a physical Windows audio endpoint.
    # Dedicated audio_editor/multi_audio cases retain the hardware-driver checks.
    args=command('tests/contact_selection_smoke.gd',extra=['--audio-driver','Dummy','--',str(folder),reference]);p=subprocess.run(args,cwd=ROOT,capture_output=True,encoding='utf-8',errors='replace',timeout=200);text=p.stdout+p.stderr;(folder/'engine.log').write_text(text,encoding='utf-8')
    assert p.returncode==0 and 'CONTACT_SELECTION ' in text and not any(x in text for x in ['ERROR:','FAIL ','ObjectDB instances leaked','_set_transient_exclusive_child']),text
    r=json.loads((folder/'result.json').read_text());assert r['failures']==0 and len(r['native_reports'])==5 and r['audio_driver']=='Dummy'
    receipt=Path(args[args.index('--receipt')+1]);v=json.loads(receipt.read_text());assert v['exit']==0 and v['child_desktop_confirmed'] and not v['foreground_child_observed'] and v['job_closed'] and v['desktop_closed'];r['private_receipt']=str(receipt);r['reference_project']=reference;(ROOT/'output/contact-selection-verification.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
if __name__=='__main__':main()
