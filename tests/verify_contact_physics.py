"""Hidden Windows body/secondary/contact interval transition checks."""
from pathlib import Path
import json, subprocess, sys, time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command

def main():
    components='--components' in sys.argv
    label='component-contact-physics' if components else 'contact-physics'
    folder=ROOT/'output'/label/str(time.time_ns());folder.mkdir(parents=True)
    args=command('tests/contact_physics_smoke.gd',extra=['--',str(folder),*(['--components'] if components else [])])
    process=subprocess.run(args,cwd=ROOT,capture_output=True,encoding='utf-8',errors='replace',timeout=160)
    output=process.stdout+process.stderr;(folder/'engine.log').write_text(output,encoding='utf-8')
    assert process.returncode==0 and 'CONTACT_PHYSICS ' in output and not any(x in output for x in ['ERROR:','FAIL ','ObjectDB instances leaked','_set_transient_exclusive_child']),output
    result=json.loads((folder/'result.json').read_text());assert result['failures']==0
    if components: assert result['native_tested'], 'Component recording acceptance requires the retained native VRM fixture'
    if result['native_tested']:
        probe=json.loads(subprocess.check_output([r'C:\Program Files\ffmpeg\bin\ffprobe.exe','-v','error','-count_frames','-show_streams','-show_format','-of','json',result['movie']],text=True))
        video=next(x for x in probe['streams'] if x['codec_type']=='video')
        assert (video['codec_name'],video['width'],video['height'],video['r_frame_rate'],video['nb_read_frames'])==('h264',1920,1080,'24/1','48')
        assert abs(float(probe['format']['duration'])-2)<.001
    receipt=Path(args[args.index('--receipt')+1]);value=json.loads(receipt.read_text())
    assert value['exit']==0 and value['child_desktop_confirmed'] and not value['foreground_child_observed'] and value['job_closed'] and value['desktop_closed']
    result['private_receipt']=str(receipt);(ROOT/'output'/(label+'-verification.json')).write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main()
