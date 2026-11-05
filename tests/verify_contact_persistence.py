"""Actual five-native contact worlds across HAS, cold recovery and lesson snapshots."""
from pathlib import Path
import array,hashlib,json,math,subprocess,sys,time,wave
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command
def main():
    resume=len(sys.argv)>1
    folder=Path(sys.argv[1]).resolve() if resume else ROOT/'output/contact-persistence'/str(time.time_ns())
    assert folder.resolve().is_relative_to((ROOT/'output/contact-persistence').resolve())
    if not resume:folder.mkdir(parents=True)
    samples=array.array('h',(int(11314*math.sin(2*math.pi*1000*n/44100)) for n in range(44100)))
    if sys.byteorder!='little':samples.byteswap()
    if not resume:
        with wave.open(str(folder/'tone.wav'),'wb') as wav:wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(44100);wav.writeframes(samples.tobytes())
    receipts=[]
    def run(script,args,label,timeout):
        commandline=command(script,extra=args if script is None else ['--',*args]);p=subprocess.run(commandline,cwd=ROOT,capture_output=True,encoding='utf-8',errors='replace',timeout=timeout)
        text=p.stdout+p.stderr;(folder/(label+'.log')).write_text(text,encoding='utf-8')
        assert p.returncode==0 and not any(x in text for x in ['ERROR:','FAIL ','ObjectDB instances leaked','_set_transient_exclusive_child']),text
        receipt=Path(commandline[commandline.index('--receipt')+1]);r=json.loads(receipt.read_text());assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'];receipts.append(str(receipt))
    if resume:
        # Adopt only this terminal writer, not the failed script-mode reader.
        text=(folder/'writer.log').read_text(encoding='utf-8');marker=next(x for x in text.splitlines() if x.startswith('CONTACT_PERSISTENCE_WRITE '));adopted=json.loads(marker.removeprefix('CONTACT_PERSISTENCE_WRITE '))
        assert adopted==json.loads((folder/'writer-result.json').read_text()) and adopted['failures']==0 and not any(x in text for x in ['ERROR:','FAIL ','ObjectDB instances leaked'])
        assert not subprocess.check_output(['git','diff','--name-only','HEAD','--','src'],cwd=ROOT,text=True).strip(),'Do not adopt writer evidence across production edits'
        assert (ROOT/'tests/contact_persistence_smoke.gd').stat().st_mtime <= (folder/'writer-result.json').stat().st_mtime
        candidates=[p for p in (ROOT/'output/private-desktop').glob('contact_persistence_smoke_*.json') if folder.stat().st_ctime<=p.stat().st_mtime<=(folder/'writer-result.json').stat().st_mtime+3]
        assert len(candidates)==1,candidates
        r=json.loads(candidates[0].read_text());assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'];receipts.append(str(candidates[0]))
        (folder/'writer-adoption.json').write_text(json.dumps({'terminal_writer_only':True,'failed_reader_not_adopted':True,'receipt':str(candidates[0]),'writer_log_sha256':hashlib.sha256((folder/'writer.log').read_bytes()).hexdigest(),'writer_source_sha256':hashlib.sha256((ROOT/'tests/contact_persistence_smoke.gd').read_bytes()).hexdigest(),'production_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'src').glob('*') if p.is_file()}},indent=2))
    else:run('tests/contact_persistence_smoke.gd',[str(folder)],'writer',220)
    writer=json.loads((folder/'writer-result.json').read_text());assert writer['failures']==0
    scene=folder/'reader.tscn';scene.write_text('[gd_scene load_steps=3 format=3]\n[ext_resource type="Script" path="res://tests/contact_persistence_app.gd" id="1"]\n[ext_resource type="Script" path="res://tests/contact_persistence_read.gd" id="2"]\n[node name="Studio" type="Control"]\nlayout_mode=3\nanchors_preset=15\nanchor_right=1.0\nanchor_bottom=1.0\ngrow_horizontal=2\ngrow_vertical=2\nscript=ExtResource("1")\n[node name="Observer" type="Node" parent="."]\nscript=ExtResource("2")\n',encoding='utf-8')
    if (folder/'linked.log').exists():(folder/'linked-script-mode-failed.log').write_bytes((folder/'linked.log').read_bytes())
    run(None,[str(scene),'--',str(folder),'linked'],'linked',180)
    # Only our fresh owned GLB input directory moves. Owner/native originals stay put.
    source=folder/'sources';held=folder/'sources-held';assert source.resolve().is_relative_to(folder.resolve()) and held.resolve().is_relative_to(folder.resolve()) and source.is_dir() and not held.exists();source.rename(held)
    for mode in ['packed','recovery','lesson']:run(None,[str(scene),'--',str(folder),mode],mode,180)
    reports={mode:json.loads((folder/('reader-'+mode+'.json')).read_text()) for mode in ['linked','packed','recovery','lesson']}
    for movie in [writer['movie'],reports['packed']['movie']]:
        probe=json.loads(subprocess.check_output([r'C:\Program Files\ffmpeg\bin\ffprobe.exe','-v','error','-count_frames','-show_streams','-show_format','-of','json',movie],text=True));v=next(x for x in probe['streams'] if x['codec_type']=='video');assert (v['codec_name'],v['width'],v['height'],v['r_frame_rate'],v['nb_read_frames'])==('h264',1920,1080,'24/1','48');assert abs(float(probe['format']['duration'])-2)<.001 and any(x.get('codec_name')=='aac' for x in probe['streams'])
        pcm=subprocess.check_output([r'C:\Program Files\ffmpeg\bin\ffmpeg.exe','-v','error','-i',movie,'-vn','-f','s16le','-ac','1','-ar','48000','-']);decoded=array.array('h');decoded.frombytes(pcm)
        if sys.byteorder!='little':decoded.byteswap()
        onset=next(i for i,x in enumerate(decoded) if abs(x)>1000)/48000;assert abs(onset-1)<.002
    for path,sha in writer['source_hashes'].items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==sha,path
    result={'writer':writer,'readers':reports,'private_receipts':receipts,'audio_onset_seconds':onset};(ROOT/'output/contact-persistence-verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main()
