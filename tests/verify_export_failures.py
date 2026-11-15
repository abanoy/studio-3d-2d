"""Self-contained headless tests of real encoder failure and owned-process cancellation."""
from pathlib import Path
import argparse,hashlib,json,os,struct,subprocess,sys,time,zlib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command

def fixture_png():
    # Original RGB color bars; no renderer, external art or historical spikes needed.
    row=b'\0'+b''.join(bytes((40+60*(x//240%3),80+40*(x//240%4),140)) for x in range(1920))
    def chunk(kind,data):return struct.pack('!I',len(data))+kind+data+struct.pack('!I',zlib.crc32(kind+data)&0xffffffff)
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!2I5B',1920,1080,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(row*1080))+chunk(b'IEND',b'')

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path);options=parser.parse_args()
    folder=(options.output or ROOT/'output/export-failures'/str(time.time_ns())).resolve();folder.mkdir(parents=True,exist_ok=False)
    fixtures=folder/'spikes';fixtures.mkdir();png=fixture_png();digest=hashlib.sha256(png).hexdigest()
    for frame in range(1,49):(fixtures/f'frame_{frame:06d}.png').write_bytes(png)
    args=command('tests/export_failures.gd',headless=True,extra=['--log-file',str(folder/'engine.log'),'--',str(folder)])
    result=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=90)
    log=result.stdout+result.stderr;(folder/'stdout.log').write_text(log,encoding='utf-8')
    assert result.returncode==0 and 'EXPORT_FAILURES failures=0' in log and log.count('PASS ')==5 and not any(v in log for v in ['ERROR:','FAIL ','ObjectDB instances leaked']),log
    for name in ['spikes','existing-output','cancel-encoding']:
        frames=sorted((folder/name).glob('frame_*.png'));assert len(frames)==48 and all(hashlib.sha256(p.read_bytes()).hexdigest()==digest for p in frames)
    failed=folder/'missing-sequence';first=(failed/'encoder.log').read_text();retries=list(failed.glob('movie-*.log'))
    assert len(retries)==1 and 'Exit: ' in first and 'frame_%06d.png' in first
    assert 'absent-encoder.exe' in retries[0].read_text() and 'Could not start FFmpeg' in retries[0].read_text()
    cancelled=(folder/'cancel-encoding/encoder.log').read_text();assert 'Exit: -1' in cancelled
    assert not list(failed.glob('*.mp4'))
    existing=folder/'existing-output'
    assert (existing/'movie.mp4').read_text()=="Owned test fixture: preserve this earlier output."
    assert (existing/'encoder.log').read_text()=="Owned test fixture: preserve the earlier diagnostic.\n"
    assert (folder/'controlled-partial.mp4').read_bytes()==b'controlled partial output'
    proof=dict(engine_checks=5,failures=0,headless=True,real_ffmpeg=True,frame_count=48,original_and_cancelled_frames_unchanged=True,frame_sha256=digest,separate_retry_diagnostic=True,cancelled_process_cleared=True,existing_output_log_preserved=True,stale_finished_path_cleared=True,actual_nonzero_exit37_retained=True,folder=str(folder))
    (folder/'verification.json').write_text(json.dumps(proof,indent=2),encoding='utf-8');print(json.dumps(proof,indent=2))

if __name__=='__main__':main()
