"""Bounded protected native packed/cold and four-frame1080p24 movie check."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1]
sys.dont_write_bytecode=True
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tools'),str(ROOT)]
import verify_import_capability as V
import secondary_reconstruction as R

def sha(raw):return hashlib.sha256(raw).hexdigest()
def pin(path):return (V.identity(path.lstat()),sha(V.read(path)))
def probe_movie(path,encoder,folder):
    selected=Path(encoder) if Path(encoder).is_absolute() else Path(shutil.which(encoder) or '')
    probe=selected.with_name('ffprobe.exe');V.need(probe.is_file(),'Existing FFprobe sibling required');before=pin(probe)
    process=None;record={'status':'FAIL'}
    try:
        with (folder/'ffprobe-stdout.json').open('xb') as out,(folder/'ffprobe-stderr.log').open('xb') as err:
            process=subprocess.Popen([str(probe),'-v','error','-count_frames','-show_streams','-of','json',str(path)],stdin=subprocess.DEVNULL,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
            record['pid']=process.pid
            try:record['exit']=process.wait(timeout=30)
            finally:
                if process.poll() is None:process.kill();process.wait(timeout=5)
            record['reaped']=process.returncode is not None
        V.need(process.returncode==0 and not V.read(folder/'ffprobe-stderr.log'),'FFprobe failed')
        streams=json.loads(V.read(folder/'ffprobe-stdout.json'))['streams'];video=[s for s in streams if s.get('codec_type')=='video']
        V.need(len(video)==1 and (video[0]['codec_name'],video[0]['width'],video[0]['height'],video[0]['r_frame_rate'],video[0]['nb_read_frames'])==('h264',1920,1080,'24/1','4'),'Exact actual four-frame1080p24 H264 stream required')
        record.update(status='PASS',checks=1,stream={k:video[0][k] for k in ('codec_name','width','height','r_frame_rate','nb_read_frames','duration')})
    finally:
        if process is not None:
            if process.poll() is None:process.kill();process.wait(timeout=5)
            process._handle.Close();record['handle_closed']=True
        record['tool_preserved']=pin(probe)==before
        (folder/'ffprobe-result.json').write_text(json.dumps(record,indent=2)+'\n')
    V.need(record['status']=='PASS' and record['tool_preserved'],'FFprobe contract failed');return record

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);o=p.parse_args();V.need(os.name=='nt','Approved private Windows runtime required')
    original=V.safe(o.source).resolve(strict=True);original_pin=pin(original)
    V.need(original_pin[1]=='a329cd47bd74b05278a6e501b9503d8e0b9231bf6adc647307d573170166a3ec','Exact protected Junko source required')
    folder=ROOT/'output'/('reconstructed-rest-movie-'+str(time.time_ns()));folder.mkdir();(folder/'Cases').mkdir();inputs=folder/'Input';inputs.mkdir()
    source=inputs/'original.glb';V.new(source,V.read(original));g=R.H.GLB(source)
    request={'source_sha256':g.sha,'reviewed':True,'node':131,'primitive':1,'component':2,'segments':4,'reconstruct_weights':True}
    candidate=Path(R.build(source,inputs/'Candidate',request)['glb']);inputs_before=V.inventory(inputs)
    frozen,blobs=V.source_blobs();environment=dict(os.environ);result={'status':'FAIL','cases':[],'whole_full_claimed':False,'whole_back_hair_complete':False,'source_arrays_or_art_published':False};runtime=None;reader=None;primary=None
    try:
        runtime=V.studio(folder,'WriterStudio',blobs)
        writer=V.run_case(folder,'writer',runtime,'tests/reconstructed_rest_movie_smoke.gd','RECONSTRUCTED_REST_MOVIE_WRITE ',19,[str(source),str(candidate)],False,result,None)
        data=Path(writer['data']);project=data/'Reconstructed hair four frames.has';expected=data/'expected.var'
        V.need(Path(writer['report'].get('packed','')).resolve()==project.resolve() and writer['report'].get('frames')==4 and writer['report'].get('source_arrays_published') is False,'Actual packed writer scope differs')
        movie=V.safe(Path(writer['report']['movie'])).resolve(strict=True);V.need(movie.is_relative_to(data) and movie.name=='movie.mp4','Movie must remain in writer-owned data')
        result['movie_probe']=probe_movie(movie,writer['report']['encoder'],folder)
        handoff=folder/'Handoff';handoff.mkdir();handoff_pins={}
        for path in (project,expected):
            raw=V.read(path);V.new(handoff/path.name,raw);handoff_pins[path.name]=sha(raw)
        reader=V.studio(folder,'ReaderStudio',blobs)
        with V.writer_offline(folder,[runtime,data,Path(writer['user']),inputs],result):
            V.run_case(folder,'reader',reader,'tests/reconstructed_rest_movie_smoke.gd','RECONSTRUCTED_REST_MOVIE_READ ',10,[str(handoff/project.name),str(handoff/expected.name),'--read'],False,result,None)
            V.need(all(sha(V.read(handoff/name))==digest for name,digest in handoff_pins.items()),'Cold handoff changed')
        result['status']='PASS';result['owner_review_project']=str(project);result['handoff_sha256']=handoff_pins
    except BaseException as issue:primary=issue;result['error']=str(issue)
    finally:
        result['checks']=sum(row.get('checks',0) for row in result['cases'])+result.get('movie_probe',{}).get('checks',0);result['source_preservation_failures']=V.sources_unchanged(frozen);result['parent_environment_preserved']=dict(os.environ)==environment;result['original_source_preserved']=pin(original)==original_pin
        result['owned_inputs_preserved']=inputs.exists() and V.inventory(inputs)==inputs_before
        result['runtime_sources_preserved']=all(stage is None or all(V.read(stage/name)==raw for name,raw in blobs.items()) for stage in (runtime,reader))
        result['all_private_resources_closed']=bool(result['cases']) and all(row.get('private_resources_closed') is True and row.get('launcher_reaped') is True and row.get('launcher_handle_closed') is True for row in result['cases'])
        if result['source_preservation_failures'] or not all(result[k] for k in ('parent_environment_preserved','original_source_preserved','owned_inputs_preserved','runtime_sources_preserved','all_private_resources_closed')):result['status']='FAIL'
        (folder/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'checks':result['checks'],'result':str(folder/'verification.json')}))
    if primary:raise primary
    return 0 if result['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
