"""Freeze current source and review it cold, without copying development caches."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import time
import zipfile

ROOT=Path(__file__).resolve().parents[1]
def read(path):return json.loads(Path(path).read_bytes())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoint',type=Path,help='Optional checksum-bound source inventory; defaults to the current Git checkout inventory')
    parser.add_argument('--checkpoint-sha256',default='b38d7aae02db1b79f3a293968d9a4817d50282a46676d9b9188920ab2be65ca5')
    parser.add_argument('--inventory-only',action='store_true',help='Report frozen source hashes without running or certifying cold review')
    options=parser.parse_args();prior=options.checkpoint
    if prior is not None:
        assert sha(prior)==options.checkpoint_sha256
        with zipfile.ZipFile(prior) as z:names=z.namelist()
    else:
        names=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=ROOT).decode('utf-8').split('\0')
        names=[n for n in names if n and Path(n).parts[0] not in ('output','.godot','.git','__pycache__') and '__pycache__' not in Path(n).parts and not n.endswith('.pyc')]
    names=sorted(set(names+['tests/current_candidate_smoke.gd','tests/current_candidate_startup.gd','tests/current_candidate_startup.tscn','tests/verify_current_candidate.py','docs/current_candidate_2026-11-04.md']))
    assert len(names)>=593 and all(not Path(n).is_absolute() and '..' not in Path(n).parts and Path(n).parts[0] not in ('output','.godot','.git') for n in names)
    required={str(p.relative_to(ROOT)).replace('\\','/') for p in (ROOT/'src').rglob('*.gd')}
    assert required.issubset(names),'The checkpoint inventory omits current app scripts. Pass the latest checkpoint and its SHA256 explicitly.'
    source={n:(ROOT/n).read_bytes() for n in names};hashes={n:hashlib.sha256(b).hexdigest() for n,b in source.items()}
    if options.inventory_only:
        print(json.dumps({'scope':'source inventory only; no runtime or historical-reader acceptance','files':len(source),'source_hashes':hashes},indent=2))
        return
    token=str(time.time_ns());folder=ROOT/'output/current-candidate'/token;folder.mkdir(parents=True)
    (folder/'source-inputs.json').write_text(json.dumps(hashes,indent=2),encoding='utf-8')
    receipts=[];steps=[];cases=[];originals={}
    def clone(kind):
        target=folder/('Moved Studio — тест '+kind)
        for n,data in source.items():
            path=target/n;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
        profile='Hybrid Animation Studio Review '+token+' '+kind
        override='[application]\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir_name='+json.dumps(profile)+'\n'
        (target/'override.cfg').write_text(override,encoding='utf-8')
        assert not (target/'output').exists() and not (target/'.godot').exists()
        return target,profile
    def module_at(target):
        spec=importlib.util.spec_from_file_location('review_run_'+str(len(steps)),target/'run.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
    def run(target,args,label,marker,timeout=200):
        started=time.time_ns();before=set((target/'output/private-desktop').glob('*.json'))
        result=subprocess.run(args,cwd=target,capture_output=True,timeout=timeout,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        data=result.stdout+result.stderr;(folder/(label+'.log')).write_bytes(data)
        steps.append({'label':label,'exit':result.returncode,'started_ns':started,'args':list(map(str,args))})
        (folder/'steps.json').write_text(json.dumps(steps,indent=2),encoding='utf-8')
        fresh=set((target/'output/private-desktop').glob('*.json'))-before
        assert result.returncode==0 and fresh and marker.encode() in data and not any(s in data for s in (b'ERROR:',b'FAIL ',b'ObjectDB instances leaked')),data.decode('utf-8',errors='replace')
        for path in fresh:
            record=read(path);assert record['exit']==0 and record['child_desktop_confirmed'] and not record['foreground_child_observed'] and record['job_closed'] and record['desktop_closed'],record
            receipts.append(str(path))
        assert all(sha(target/n)==digest for n,digest in hashes.items())
        print('PASS cold review '+label,flush=True)
    beginner,profile=clone('beginner')
    run(beginner,[sys.executable,'-u','tests/verify_first_movie.py'],'beginner','"results":',timeout=330)
    course=read(beginner/'output/first-movie-verification.json')
    edge,edge_profile=clone('audio-edge')
    run(edge,[sys.executable,'-u','tests/verify_audio_edge.py'],'audio-edge','PASS sound end handle',timeout=200)
    audio_edge=read(edge/'output/audio-edge-verification.json')
    # A declared previous-reader fixture is test input, never an application
    # asset or a hidden dependency on a development import cache.
    previous=Path('C:/a/Programming/cloudflare/prototypes/studio-3d-2d/output/checkpoints/2026-11-04-035230-joint-sound-review/development-source.zip')
    assert sha(previous)=='159d24e47093f77fc532a608ff45beca00f8489fe5c8b85443557c44b2ead042'
    previous_audio=folder/'previous_audio.gd'
    with zipfile.ZipFile(previous) as z:previous_audio.write_bytes(z.read('src/audio_track.gd'))
    fades,fade_profile=clone('audio-fades')
    run(fades,[sys.executable,'-u','tests/verify_audio_fades.py','--previous-audio',str(previous_audio)],'audio-fades','PASS sound fades',timeout=330)
    audio_fades=read(fades/'output/audio-fades-verification.json')
    images,images_profile=clone('png-export')
    run(images,[sys.executable,'-u','tests/verify_png_export.py'],'png-export','PASS PNG-only',timeout=210)
    png_export=read(images/'output/png-export-verification.json')
    previous_storage=folder/'previous_storage.gd'
    old=Path('C:/a/Programming/cloudflare/prototypes/studio-3d-2d/output/checkpoints/2026-11-04-134345-media-review/development-source.zip')
    assert sha(old)=='03e81a97979398819c33055416ccf5667fd616d9d1b18307d25c3d0e7042352e'
    with zipfile.ZipFile(old) as z:previous_storage.write_bytes(z.read('src/storage.gd'))
    timing,timing_profile=clone('project-rate')
    run(timing,[sys.executable,'-u','tests/verify_project_timing.py','--previous-storage',str(previous_storage)],'project-rate','PASS project rate presets',timeout=300)
    project_rate=read(timing/'output/project-timing-verification.json')
    length,length_profile=clone('project-duration')
    run(length,[sys.executable,'-u','tests/verify_project_duration.py'],'project-duration','"fresh_readers":',timeout=300)
    project_duration=read(length/'output/project-duration-verification.json')
    native_orbit=Path(next(c['project'] for c in read(ROOT/'output/joint-authoring-verification.json')['cases'] if c['label']=='miku'))
    orbit_input=folder/'Orbit native.has';orbit_input.write_bytes(native_orbit.read_bytes());originals[str(native_orbit)]=sha(native_orbit)
    orbit,orbit_profile=clone('orbit')
    run(orbit,[sys.executable,'-u','tests/verify_orbit_navigation.py','--native-project',str(orbit_input)],'orbit','PASS optional orbit',timeout=240)
    orbit_navigation=read(orbit/'output/orbit-navigation-verification.json')
    trim=read(ROOT/'output/audio-trim-verification.json');mmd=read(ROOT/'output/mmd-ik-verification.json');legacy=read(ROOT/'output/contact-persistence-verification.json')['writer'];motion=read(ROOT/'output/motion-animation-app-verification.json')
    specifications=[
        ('trim',Path(trim['packed']),Path(trim['movie']).parent/'frame_000025.png',24,read(Path(trim['folder'])/'expected.json')['mix']),
        ('mmd',Path(mmd['project']),Path(mmd['movie']).parent/'frame_000021.png',20,''),
        ('native',Path(legacy['packed']),Path(legacy['folder'])/'reference.png',12,''),
        ('assisted',Path(motion['project']),Path(motion['folder'])/'saved-frame.png',10,''),
        ('fade',Path(audio_fades['project']),Path(audio_fades['movie']).parent/'frame_000025.png',24,audio_fades['mix']),
        ('rate',Path(project_rate['project']),Path(project_rate['movie']).parent/'frame_000025.png',24,project_rate['mix']),
        ('duration',Path(project_duration['project']),Path(project_duration['movie']).parent/'frame_000013.png',12,project_duration['mix']),
    ]
    authoring=read(ROOT/'output/joint-authoring-verification.json')
    for case in authoring['cases']:
        specifications.append(('joint-'+case['label'],Path(case['project']),Path(authoring['folder'])/(case['label']+'-pose.png'),12,''))
    for kind,project,reference,frame,mix in specifications:
        inputs=folder/'inputs'/kind;inputs.mkdir(parents=True)
        for path,name in [(project,'Scene.has'),(reference,'Reference.png')]:
            originals[str(path)]=sha(path);(inputs/name).write_bytes(path.read_bytes())
        with zipfile.ZipFile(project) as z:manifest=json.loads(z.read('project.json'))
        assert manifest['schema_version'] in (4,5)
        (inputs/'manifest.json').write_text(json.dumps(manifest),encoding='utf-8')
        target,profile=clone(kind)
        # First launch happens only after moving the complete source directory.
        moved=folder/('Relocated '+target.name);assert target.resolve().is_relative_to(folder.resolve()) and moved.resolve().is_relative_to(folder.resolve());target.rename(moved);target=moved
        assert not (target/'output').exists() and not (target/'.godot').exists()
        config={'kind':kind,'profile':profile,'project':str(inputs/'Scene.has'),'reference':str(inputs/'Reference.png'),'manifest':str(inputs/'manifest.json'),'frame':frame,'mix':mix}
        (inputs/'case.json').write_text(json.dumps(config),encoding='utf-8')
        args=module_at(target).command('tests/current_candidate_smoke.gd',extra=['--',str(inputs/'case.json')])
        run(target,args,kind,'CURRENT_CANDIDATE ')
        report=read(target/'output/current-review/result.json');assert report['failures']==0
        ffprobe=os.environ.get('HYBRID_FFPROBE',r'C:\Program Files\ffmpeg\bin\ffprobe.exe')
        result=subprocess.run([ffprobe,'-v','error','-count_frames','-show_streams','-show_format','-of','json',report['movie']],capture_output=True,check=True)
        media=json.loads(result.stdout);video=next(s for s in media['streams'] if s['codec_type']=='video')
        expected_video=manifest['video'];rate=f"{int(expected_video['fps_num'])}/{int(expected_video['fps_den'])}"
        assert (video['codec_name'],video['width'],video['height'],video['r_frame_rate'],video['nb_read_frames'])==('h264',expected_video['width'],expected_video['height'],rate,str(int(expected_video['duration_frames'])))
        assert abs(float(media['format']['duration'])-expected_video['duration_frames']*expected_video['fps_den']/expected_video['fps_num'])<.001
        if manifest.get('audio'):assert any(s.get('codec_name')=='aac' for s in media['streams'])
        (folder/(kind+'-ffprobe.json')).write_bytes(result.stdout);cases.append(report)
    assert all(sha(Path(path))==digest for path,digest in originals.items())
    startup,profile=clone('normal-home')
    run(startup,module_at(startup).command(extra=['res://tests/current_candidate_startup.tscn','--',str(folder/'normal-startup.json')]),'normal-home','CURRENT_REVIEW_STARTUP ')
    startup_result=read(folder/'normal-startup.json');assert startup_result['home_visible'] and startup_result['simple'] and startup_result['empty'] and startup_result['profile'].replace('\\','/').endswith(profile)
    # A clean, never-used copy is the publication candidate; only normal startup
    # is exercised here, with its own profile and no test script/app flags.
    candidate,profile=clone('owner')
    run(candidate,module_at(candidate).command(extra=['--quit-after','8']),'startup','Godot Engine')
    result={'folder':str(folder),'candidate':str(candidate),'profile':profile,'source_files':len(source),'source_input_hashes':str(folder/'source-inputs.json'),'cases':cases,'beginner':course,'audio_edge':audio_edge,'audio_fades':audio_fades,'png_export':png_export,'project_rate':project_rate,'project_duration':project_duration,'orbit_navigation':orbit_navigation,'startup':startup_result,'private_receipts':receipts,'original_inputs_unchanged':True,'functional_unchanged':True,'steps':steps}
    (folder/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    (ROOT/'output/current-candidate-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print('PASS frozen cache-free review, beginner/resume, audio3/native/MMD, resave/movies, isolated profile and normal startup')
if __name__=='__main__':main()
