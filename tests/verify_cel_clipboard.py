"""Real drawing timeline copy/cut/paste, immutable pixels, Undo, cold HAS and MP4."""
from pathlib import Path
import argparse,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import configure_private_display,command

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--isolated-display',help='Linux: explicitly provisioned private dummy X display')
    parser.add_argument('--output',type=Path)
    options=parser.parse_args()
    if os.name!='nt':
        if sys.platform!='linux' or not options.isolated_display:parser.error('Linux requires a private --isolated-display; no shared-desktop fallback')
        configure_private_display(options.isolated_display)
    folder=(options.output or ROOT/'output/cel-clipboard'/str(time.time_ns())).resolve();folder.mkdir(parents=True,exist_ok=False)
    reports={};receipts=[]
    def run(script,label,marker,extra=(),headless=False):
        args=command(script,headless=headless,extra=(['--audio-driver','Dummy'] if os.name!='nt' else [])+['--log-file',str(folder/(label+'-engine.log')),'--',str(folder),*extra])
        result=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=165)
        log=result.stdout+result.stderr;(folder/(label+'.log')).write_text(log,encoding='utf-8')
        assert result.returncode==0 and marker in log and not any(s in log for s in ['ERROR:','FAIL ','ObjectDB instances leaked']),log
        reports[label]=json.loads(next(s[len(marker):] for s in log.splitlines() if s.startswith(marker)));assert reports[label]['failures']==0
        if os.name=='nt' and not headless:
            path=Path(args[args.index('--receipt')+1]);r=json.loads(path.read_bytes());assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'];receipts.append(str(path))
    run('tests/cel_clipboard_unit.gd','unit','CEL_CLIPBOARD_UNIT ',headless=True)
    run('tests/cel_clipboard_smoke.gd','writer','CEL_CLIPBOARD_SMOKE ')
    packed=(folder/'clipboard.has').read_bytes();(folder/'writer-cache').rename(folder/'writer-cache.offline')
    run('tests/cel_clipboard_smoke.gd','reader','CEL_CLIPBOARD_READ ',['--read'])
    assert (folder/'clipboard.has').read_bytes()==packed
    ffmpeg=os.environ.get('HYBRID_FFMPEG','ffmpeg');probe=str(Path(ffmpeg).with_name('ffprobe.exe' if os.name=='nt' else 'ffprobe'))
    media=json.loads(subprocess.check_output([probe,'-v','error','-show_streams','-show_format','-of','json',reports['writer']['movie']],creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0));video=next(s for s in media['streams'] if s['codec_type']=='video')
    assert (video['codec_name'],video['width'],video['height'],video['r_frame_rate'],video['nb_frames'])==('h264',1920,1080,'24/1','48') and abs(float(media['format']['duration'])-2)<.001
    proof=dict(reports=reports,video=video,manual_has_unchanged=True,writer_cache_unavailable_for_cold_open=True,private_receipts=receipts,isolated_display=options.isolated_display,folder=str(folder));(folder/'verification.json').write_text(json.dumps(proof,indent=2),encoding='utf-8');print(json.dumps(proof,indent=2))

if __name__=='__main__':main()
