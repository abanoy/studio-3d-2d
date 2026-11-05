"""Direct target gestures in the real editor on a private Windows desktop."""
from pathlib import Path
import json, subprocess, sys, time
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from run import command

def main():
    reference = json.loads((ROOT/'output/contact-persistence-verification.json').read_text())['writer']['packed']
    folder = ROOT/'output/contact-viewport'/str(time.time_ns())
    folder.mkdir(parents=True)
    args = command('tests/contact_viewport_smoke.gd', extra=['--', str(folder), reference])
    p = subprocess.run(args, cwd=ROOT, capture_output=True, encoding='utf-8', errors='replace', timeout=200)
    text = p.stdout+p.stderr
    (folder/'engine.log').write_text(text, encoding='utf-8')
    assert p.returncode == 0 and 'CONTACT_VIEWPORT ' in text and not any(x in text for x in ['ERROR:', 'FAIL ', 'ObjectDB instances leaked', '_set_transient_exclusive_child']), text
    result = json.loads((folder/'result.json').read_text())
    assert result['failures'] == 0 and len(result['native_reports']) == 5
    receipt = Path(args[args.index('--receipt')+1])
    value = json.loads(receipt.read_text())
    assert value['exit'] == 0 and value['child_desktop_confirmed'] and not value['foreground_child_observed'] and value['job_closed'] and value['desktop_closed']
    result['private_receipt'] = str(receipt)
    result['reference_project'] = reference
    probe=json.loads(subprocess.check_output([r'C:\Program Files\ffmpeg\bin\ffprobe.exe','-v','error','-count_frames','-show_streams','-show_format','-of','json',result['movie']],text=True))
    video=next(x for x in probe['streams'] if x['codec_type']=='video')
    assert (video['codec_name'],video['width'],video['height'],video['r_frame_rate'],video['nb_read_frames'])==('h264',1920,1080,'24/1','48') and abs(float(probe['format']['duration'])-2)<.001
    args=command('tests/contact_viewport_read.gd',extra=['--',str(folder)])
    reader=subprocess.run(args,cwd=ROOT,capture_output=True,encoding='utf-8',errors='replace',timeout=100)
    output=reader.stdout+reader.stderr;(folder/'reader.log').write_text(output,encoding='utf-8')
    assert reader.returncode==0 and 'CONTACT_VIEWPORT_READ ' in output and not any(x in output for x in ['ERROR:','FAIL ','ObjectDB instances leaked']),output
    cold=json.loads((folder/'reader.json').read_text());assert cold['failures']==0
    cold_receipt=Path(args[args.index('--receipt')+1]);value=json.loads(cold_receipt.read_text())
    assert value['exit']==0 and value['child_desktop_confirmed'] and not value['foreground_child_observed'] and value['job_closed'] and value['desktop_closed']
    result['reader']={**cold,'private_receipt':str(cold_receipt)}
    (ROOT/'output/contact-viewport-verification.json').write_text(json.dumps(result, indent=2))
    print(json.dumps({k:v for k,v in result.items() if k not in ['expected_world','pose_hashes']}, indent=2))

if __name__ == '__main__':
    main()
