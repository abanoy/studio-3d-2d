"""Prepare bounded native artwork as the common RGBA8/hold clip contract.

No live scene mutation. Native layers are rendered together only after explicit
visibility choices; original source identity and exact rational timing are kept.
"""
from pathlib import Path
from fractions import Fraction
import argparse,hashlib,json,math,os,re,struct,subprocess,sys,time,zlib
try:from . import krita_assets as K
except ImportError:import krita_assets as K

MAX_SOURCE=192*1024**2
MAX_PIXELS=16_777_216
MAX_NATIVE_BYTES=512*1024**2
MAX_NORMALIZED_BYTES=256*1024**2
class Cancelled(RuntimeError):pass

def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def check_cancel(path):
    if path.exists():raise Cancelled('Artwork preparation cancelled')
def write_json(path,value):
    temporary=path.with_suffix(path.suffix+'.tmp');temporary.write_text(json.dumps(value,indent=2),encoding='utf-8')
    # Windows readers can briefly hold a non-delete-sharing handle. Keep the
    # prior complete response visible until the new atomic replacement succeeds.
    deadline=time.monotonic()+2
    while True:
        try:os.replace(temporary,path);return
        except PermissionError:
            if time.monotonic()>=deadline:raise
            time.sleep(.01)
def number(value,label,minimum,maximum):
    if type(value) is not int or not minimum<=value<=maximum:raise ValueError('Invalid '+label)
    return value

def target_indices(source_frames,source_fps,numerator,denominator):
    number(source_frames,'source duration',1,240);number(source_fps,'source frame rate',1,1000);number(numerator,'project frame-rate numerator',1,120000);number(denominator,'project frame-rate denominator',1,1001)
    rate=Fraction(numerator,denominator)
    if rate>120:raise ValueError('Project frame rate exceeds120')
    count=math.ceil(Fraction(source_frames,source_fps)*rate)
    if not 1<=count<=240:raise ValueError('Converted artwork exceeds240project frames; choose a shorter source range')
    return [int(Fraction(i*source_fps*denominator,numerator)) for i in range(count)]

def fit(source_width,source_height,width,height):
    number(source_width,'source width',1,32768);number(source_height,'source height',1,32768);number(width,'target width',1,1920);number(height,'target height',1,1080)
    ratio=min(Fraction(width,source_width),Fraction(height,source_height))
    scaled=lambda n:max(1,int(Fraction(n)*ratio+Fraction(1,2)))
    w,h=min(width,scaled(source_width)),min(height,scaled(source_height))
    return w,h,(width-w)//2,(height-h)//2

def png(path):
    if not 33<=path.stat().st_size<=128*1024**2:raise ValueError('Rendered PNG exceeds its size limit')
    with path.open('rb') as f:
        header=f.read(33)
        if header[:8]!=b'\x89PNG\r\n\x1a\n' or header[12:16]!=b'IHDR':raise ValueError('Invalid rendered PNG')
        width,height=struct.unpack('>II',header[16:24]);f.seek(8);finished=False
        while True:
            chunk=f.read(8)
            if len(chunk)!=8:break
            length,kind=struct.unpack('>I4s',chunk)
            if length>128*1024**2:raise ValueError('Excessive PNG chunk')
            crc=zlib.crc32(kind);remaining=length
            while remaining:
                data=f.read(min(65536,remaining))
                if not data:raise ValueError('Truncated PNG')
                crc=zlib.crc32(data,crc);remaining-=len(data)
            check=f.read(4)
            if len(check)!=4 or (crc&0xffffffff)!=struct.unpack('>I',check)[0]:raise ValueError('Rendered PNG checksum failed')
            if kind==b'IEND':finished=True;break
        if not finished or f.read(1):raise ValueError('Invalid PNG ending')
    if not 1<=width<=32768 or not 1<=height<=32768 or width*height>MAX_PIXELS:raise ValueError('Rendered PNG dimensions exceed the pixel budget')
    return width,height,header[24],header[25]

def run(args,folder,cancel,timeout,native=False,maximum_files=240):
    check_cancel(cancel);log=folder/('native.log' if native else 'normalize.log')
    with log.open('ab') as stream:
        process=subprocess.Popen(args,stdin=subprocess.DEVNULL,stdout=stream,stderr=stream,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        started=time.monotonic()
        try:
            while process.poll() is None:
                if cancel.exists() and not native:raise Cancelled('Artwork preparation cancelled')
                if time.monotonic()-started>timeout:raise RuntimeError('Artwork converter exceeded its time limit')
                if log.stat().st_size>2*1024**2:raise RuntimeError('Artwork converter produced too many errors')
                if native:
                    files=list((folder/'native').glob('*.png'))
                    if len(files)>maximum_files or sum(p.stat().st_size for p in files)>MAX_NATIVE_BYTES:raise RuntimeError('Native artwork render exceeded its frame/disk budget')
                time.sleep(.025)
            check_cancel(cancel)
            if process.returncode:raise RuntimeError('Artwork conversion failed; details: '+str(log))
        finally:
            if process.poll() is None:
                if native:
                    # Let the private launcher close its owned job/desktop and
                    # write a receipt even when our output budget caused failure.
                    try:cancel.write_text('stop owned converter',encoding='utf-8')
                    except OSError:pass
                    try:process.wait(timeout=5)
                    except subprocess.TimeoutExpired:process.terminate()
                else:process.terminate()
                if process.poll() is None:
                    try:process.wait(timeout=5)
                    except subprocess.TimeoutExpired:process.kill();process.wait(timeout=5)

def normalize(source,destination,ffmpeg,source_size,output_size,folder,cancel):
    w,h,x,y=fit(*source_size,*output_size)
    filters=f'format=gbrapf32le,premultiply=inplace=1:planes=7,scale={w}:{h}:flags=lanczos,unpremultiply=inplace=1:planes=7,format=rgba,pad={output_size[0]}:{output_size[1]}:{x}:{y}:color=black@0,setsar=1'
    args=[str(ffmpeg),'-nostdin','-hide_banner','-v','error','-xerror','-n','-protocol_whitelist','file','-i',str(source),'-frames:v','1','-an','-sn','-dn','-map_metadata','-1','-filter_threads','1','-vf',filters,'-c:v','png','-threads','1','-update','1',str(destination)]
    run(args,folder,cancel,30)
    width,height,depth,kind=png(destination)
    if (width,height,depth,kind)!=(*output_size,8,6):raise ValueError('Converter did not produce full-frame RGBA8 artwork')
    return {'width':w,'height':h,'x':x,'y':y}

def prepare(request):
    if not isinstance(request,dict):raise ValueError('Invalid artwork preparation request')
    source=Path(request['source']);cancel=Path(request['cancel']);check_cancel(cancel)
    if str(source).startswith(('\\\\','//')) or '://' in str(source):raise ValueError('Choose a local Krita source')
    if source.stat().st_size>MAX_SOURCE:raise ValueError('Native artwork preparation currently accepts sources up to192MiB')
    if request.get('source_sha256')!=sha(source):raise ValueError('Krita source changed since layer review; inspect it again')
    inventory=K.inspect(source);identity=inventory['source_sha256']
    if request.get('source_sha256')!=identity:raise ValueError('Krita source changed since layer review; inspect it again')
    if inventory['width']*inventory['height']>MAX_PIXELS or len(inventory['layers'])>128 or inventory['native_member_bytes']>2*1024**3:raise ValueError('Krita canvas/layers/payload exceed current preparation limits')
    if inventory['color_space'] not in ('RGBA','GRAYA'):raise ValueError('This Krita color space needs an explicit conversion in Krita first')
    maximum=number(request.get('max_cels',32),'available cel count',1,32)
    width=number(request.get('width',1920),'output width',1,1920);height=number(request.get('height',1080),'output height',1,1080)
    num=number(request['fps_num'],'frame-rate numerator',1,120000);den=number(request['fps_den'],'frame-rate denominator',1,1001)
    if Fraction(num,den)>120:raise ValueError('Project frame rate exceeds120')
    if inventory['animated']:
        if 'range' not in inventory or 'fps' not in inventory:raise ValueError('Missing native animation timing')
        frame_count=inventory['range']['frames'];indices=target_indices(frame_count,inventory['fps'],num,den)
    else:
        frame_count=1;indices=[0]*number(request.get('still_duration_frames',1),'still exposure',1,240)
    if len(indices)>number(request['available_frames'],'remaining project frames',1,240):raise ValueError('Artwork extends beyond the scene; extend Scene length or import earlier')
    krita=Path(request['krita']);ffmpeg=Path(request['ffmpeg'])
    if not krita.is_file() or not ffmpeg.is_file():raise ValueError('Installed Krita and FFmpeg are required for this preparation')
    folder=Path(request['output']).resolve()
    if folder.exists():raise ValueError('Artwork preparation needs a fresh output directory')
    folder.mkdir(parents=True);native=folder/'native';native.mkdir();images=folder/'images';images.mkdir()
    try:
        check_cancel(cancel);visibility=request.get('layer_visibility',{})
        if not isinstance(visibility,dict):raise ValueError('Invalid explicit layer visibility choices')
        write_json(folder/'progress.json',{'stage':'reviewed-copy'})
        render_source=K.render_copy(inventory,visibility,folder/'reviewed-source.kra',lambda:check_cancel(cancel)) if visibility else Path(inventory['source'])
        write_json(folder/'progress.json',{'stage':'render','frames':frame_count})
        export=native/('frame.png' if inventory['animated'] else 'still.png');receipt=folder/'private-desktop.json'
        args=[sys.executable,str(Path(__file__).with_name('private_desktop.py')),'--receipt',str(receipt),'--timeout','180','--cancel-file',str(cancel),'--memory-limit-mib','3072','--',str(krita),'--nosplash','--export-sequence' if inventory['animated'] else '--export','--export-filename',str(export),str(render_source)]
        run(args,folder,cancel,190,native=True,maximum_files=frame_count)
        placement=json.loads(receipt.read_bytes())
        if not placement.get('child_desktop_confirmed') or placement.get('foreground_child_observed') or not placement.get('job_closed') or not placement.get('desktop_closed') or placement.get('exit')!=0:raise RuntimeError('Native converter did not complete hidden-desktop verification')
        files=list(native.glob('*.png'))
        if len(files)!=frame_count:raise ValueError('Krita did not render the full expected source range')
        ordered={}
        for path in files:
            match=re.fullmatch(r'frame([0-9]+)\.png',path.name) if inventory['animated'] else None
            index=int(match[1]) if match else 0
            if inventory['animated'] and match is None or index in ordered:raise ValueError('Unexpected native sequence naming')
            if png(path)[:2]!=(inventory['width'],inventory['height']):raise ValueError('Native frame dimensions changed unexpectedly')
            ordered[index]=path
        if set(ordered)!=set(range(frame_count)):raise ValueError('Native frame numbering is not contiguous')
        by_native={};by_index={};normalized={};fit_info={};started=time.monotonic()
        for index in sorted(set(indices)):
            check_cancel(cancel)
            if time.monotonic()-started>90:raise RuntimeError('Artwork normalization exceeded90seconds')
            original=ordered[index];key=sha(original)
            if key not in by_native:
                temporary=images/('frame-%04d.png'%index);fit_info=normalize(original,temporary,ffmpeg,(inventory['width'],inventory['height']),(width,height),folder,cancel);digest=sha(temporary);target=images/(digest+'.png')
                if target.exists():temporary.unlink()
                else:temporary.rename(target)
                by_native[key]=digest;normalized[digest]={'path':'images/'+target.name,'sha256':digest,'bytes':target.stat().st_size}
                if len(normalized)>maximum or sum(r['bytes'] for r in normalized.values())>MAX_NORMALIZED_BYTES:raise ValueError('Artwork exceeds available drawing resources')
            by_index[index]=by_native[key];write_json(folder/'progress.json',{'stage':'normalize','complete':len(by_index),'total':len(set(indices))})
        holds=[]
        for target,index in enumerate(indices):
            digest=by_index[index]
            if holds and holds[-1]['sha256']==digest:holds[-1]['duration']+=1
            else:holds.append({'start':target,'duration':1,**normalized[digest]})
        if len(holds)>maximum:raise ValueError('Artwork has more held drawings than available cel slots')
        check_cancel(cancel)
        if sha(source)!=identity:raise ValueError('Original Krita source changed during preparation')
        result={'format':'studio_raster_clip_1','source':{'path':inventory['source'],'sha256':identity,'kind':'krita','width':inventory['width'],'height':inventory['height'],'fps':inventory.get('fps'),'range':inventory.get('range'),'layer_visibility':visibility},'width':width,'height':height,'fps_num':num,'fps_den':den,'duration_frames':len(indices),'fit':fit_info,'holds':holds,'native_audio_imported':False,'native_layer_editing':False,'normalization':'premultiplied RGB float Lanczos, centered RGBA8; no ICC conversion claim'}
        write_json(folder/'clip.json',result);write_json(folder/'progress.json',{'stage':'ready','holds':len(holds)});return result
    except BaseException as error:
        write_json(folder/'progress.json',{'stage':'cancelled' if isinstance(error,Cancelled) else 'error','error':str(error)})
        raise

def summary(source,cancel=None):
    if cancel:check_cancel(cancel)
    inventory=K.inspect(source,with_hash=False);reasons=[]
    if inventory['bytes']>MAX_SOURCE:reasons.append('Native rendering currently accepts sources up to192MiB')
    if inventory['width']*inventory['height']>MAX_PIXELS:reasons.append('Canvas exceeds16million pixels')
    if len(inventory['layers'])>128 or inventory['native_member_bytes']>2*1024**3:reasons.append('Layer/native payload budget exceeded')
    if inventory['animated'] and inventory.get('range',{}).get('frames',241)>240:reasons.append('Native playback range exceeds240source frames')
    if inventory['color_space'] not in ('RGBA','GRAYA'):reasons.append('Convert this color space in Krita first')
    if not reasons:inventory=K.inspect(source)
    if cancel:check_cancel(cancel)
    result={k:v for k,v in inventory.items() if k!='channels'};result.update(render_supported=not reasons,limitations=reasons)
    if len(json.dumps(result).encode())>1024*1024:raise ValueError('Layer review metadata exceeds1MiB')
    return result

def response_path(value):
    if not value:return None
    path=Path(value).resolve()
    if path.suffix.lower()!='.json' or path.exists() or not path.parent.is_dir():raise ValueError('Preparation response needs a fresh JSON file in an existing job directory')
    return path

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('request',nargs='?');parser.add_argument('--inspect');parser.add_argument('--result');parser.add_argument('--cancel-file');args=parser.parse_args()
    response=None
    try:
        if args.inspect:
            response=response_path(args.result)
            if args.request:raise ValueError('Choose either source inspection or preparation')
            result={'ok':True,'inventory':summary(args.inspect,Path(args.cancel_file) if args.cancel_file else None)}
            if response:write_json(response,result)
            print(json.dumps(result));return 0
        if not args.request:raise ValueError('Missing artwork request')
        path=Path(args.request)
        if path.stat().st_size>1024*1024:raise ValueError('Excessive artwork request')
        request=json.loads(path.read_bytes())
        if not isinstance(request,dict):raise ValueError('Invalid artwork request')
        candidate=response_path(args.result or request.get('result'))
        if candidate and candidate!=Path(request['output']).resolve().parent/'result.json':raise ValueError('Preparation response must stay in its job directory')
        response=candidate
        prepared=prepare(request);clip=Path(request['output'])/'clip.json';result={'ok':True,'status':'ready','clip':str(clip),'sha256':sha(clip),'holds':len(prepared['holds'])}
        if response:write_json(response,result)
        print(json.dumps(result));return 0
    except Exception as error:
        result={'ok':False,'status':'cancelled' if isinstance(error,Cancelled) else 'error','error':str(error)}
        if response:write_json(response,result)
        print(json.dumps(result));return 2 if isinstance(error,Cancelled) else 1

if __name__=='__main__':raise SystemExit(main())
