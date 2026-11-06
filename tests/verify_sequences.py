"""Editable sequence graph/storage/audio, real child editor, cold HAS and MP4 proof."""
import argparse
import array
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from run import configure_private_display, command


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--isolated-display',help='Linux: pre-provisioned private dummy X display')
    parser.add_argument('--output',type=Path)
    parser.add_argument('--mask-recovery',action='store_true',help='Exercise graph3 masks through real abrupt exit and ordinary startup')
    options=parser.parse_args()
    if os.name!='nt':
        if sys.platform!='linux' or not options.isolated_display:parser.error('Linux requires a private --isolated-display; no shared-desktop fallback')
        configure_private_display(options.isolated_display)
    folder=(options.output or ROOT/'output/sequences'/str(time.time_ns())).resolve()
    folder.mkdir(parents=True,exist_ok=False)
    corpus=folder/'corpus.json'
    subprocess.run([sys.executable,str(ROOT/'tests/test_sequence_graph.py'),'--corpus',str(corpus)],cwd=ROOT,check=True)
    reports={};receipts=[]
    def run(script,label,args,marker,headless=False,abrupt=False,scene=None):
        argv=command(script,headless=headless,extra=([str(scene)] if scene else [])+['--audio-driver','Dummy','--',*map(str,args)])
        result=subprocess.run(argv,cwd=ROOT,capture_output=True,timeout=290,
                              creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        raw=result.stdout+result.stderr;(folder/(label+'.log')).write_bytes(raw)
        assert result.returncode==(-9 if abrupt and os.name!='nt' else 0) and marker.encode() in raw and not any(s in raw for s in [b'ERROR:',b'FAIL ',b'ObjectDB instances leaked']),raw.decode(errors='replace')
        if os.name=='nt' and not headless:
            receipt=Path(argv[argv.index('--receipt')+1]);r=json.loads(receipt.read_bytes())
            assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'],r
            receipts.append(str(receipt))
        line=next(x for x in raw.decode(errors='replace').splitlines() if x.startswith(marker))
        report=json.loads(line[len(marker):]);assert report['failures']==0;reports[label]=report
    run('tests/sequence_graph_unit.gd','graph',[corpus],'SEQUENCE_GRAPH_UNIT ',True)
    run('tests/sequence_audio_unit.gd','audio',[],'SEQUENCE_AUDIO_UNIT ',True)
    run('tests/sequence_storage_unit.gd','storage',[folder/'storage'],'SEQUENCE_STORAGE_UNIT ',True)
    run('tests/sequence_runtime_smoke.gd','runtime',[folder/'storage'],'SEQUENCE_RUNTIME_SMOKE ')
    editor=folder/'editor';editor.mkdir()
    run('tests/sequence_editor_smoke.gd','writer',[editor,'--crash',*(['--mask-recovery'] if options.mask_recovery else [])],'SEQUENCE_EDITOR_SMOKE ',abrupt=True)
    assert not (editor/'graceful-exit.txt').exists() and not (editor/'kill-returned.txt').exists()
    preserved={str(p):p.read_bytes() for p in editor.glob('*.has')}
    run('tests/sequence_editor_smoke.gd','reader',[editor,'--read'],'SEQUENCE_EDITOR_READ ')
    scene=editor/'startup.tscn'
    scene.write_text('[gd_scene load_steps=3 format=3]\n[ext_resource type="Script" path="res://tests/sequence_startup_app.gd" id="1"]\n[ext_resource type="Script" path="res://tests/sequence_startup_observer.gd" id="2"]\n[node name="Studio" type="Control"]\nlayout_mode=3\nanchors_preset=15\nanchor_right=1.0\nanchor_bottom=1.0\ngrow_horizontal=2\ngrow_vertical=2\nscript=ExtResource("1")\n[node name="Observer" type="Node" parent="."]\nscript=ExtResource("2")\n',encoding='utf-8')
    run(None,'startup',[editor],'SEQUENCE_EDITOR_STARTUP ',scene=scene)
    assert all(Path(p).read_bytes()==blob for p,blob in preserved.items())
    ffmpeg=os.environ.get('HYBRID_FFMPEG') or shutil.which('ffmpeg')
    if not ffmpeg:raise RuntimeError('Installed FFmpeg is required')
    ffprobe=str(Path(ffmpeg).with_name('ffprobe.exe' if os.name=='nt' else 'ffprobe'))
    flags=dict(creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
    media=json.loads(subprocess.check_output([ffprobe,'-v','error','-show_streams','-show_format','-of','json',reports['writer']['movie']],**flags))
    v=next(x for x in media['streams'] if x['codec_type']=='video')
    assert (v['codec_name'],v['width'],v['height'],v['r_frame_rate'],v['nb_frames'])==('h264',1920,1080,'24/1','48')
    assert abs(float(media['format']['duration'])-2)<.001 and any(x['codec_name']=='aac' for x in media['streams'])
    pcm=array.array('h');pcm.frombytes(subprocess.check_output([ffmpeg,'-v','error','-i',reports['writer']['movie'],'-vn','-ac','1','-ar','48000','-f','s16le','pipe:1'],**flags))
    if sys.byteorder!='little':pcm.byteswap()
    onset=next(i for i,sample in enumerate(pcm) if abs(sample)>1000)/48000
    assert abs(onset-.25)<.002,onset
    for name in ['Nested packed.has','Nested linked.has','Nested editing.has']:
        with zipfile.ZipFile(editor/name) as archive:
            manifest=json.loads(archive.read('project.json'));graph=manifest['sequence_graph']
            assert manifest['schema_version']==6 and graph['format']==('studio_sequences_3' if options.mask_recovery else 'studio_sequences_1')
            assert len(graph['assets'])==1 and len(graph['clips'])==2
            child=graph['assets'][0]['scene']
            assert len(child['layers'][1]['cels'])==2 and child['world']['objects'] and child['audio']
            assert all(cel['path'] in archive.namelist() for layer in child['layers'] for cel in layer['cels'])
    result=dict(reports=reports,media=media,child_audio_onset=onset,private_receipts=receipts,
                isolated_display=options.isolated_display,mask_recovery=options.mask_recovery,native_fixtures=0,writer_abrupt_exit_verified=True,manual_has_unchanged=True,folder=str(folder))
    (folder/'verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({key:value for key,value in result.items() if key!='media'},indent=2))


if __name__=='__main__':main()
