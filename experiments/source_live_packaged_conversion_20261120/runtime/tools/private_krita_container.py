"""Run a native Krita export in an owned offline container and private Xvfb."""
from pathlib import Path
import argparse,csv,io,json,os,re,signal,subprocess,time,uuid


# This trusted program is sent as code, not interpolated document text. Xvfb's
# displayfd signals readiness directly; no shell signal/lock polling race.
START_RENDERER = r'''
from pathlib import Path
import json,os,select,subprocess,sys
config=Path('/tmp/config');config.mkdir(parents=True,exist_ok=True)
PLUGIN = r"""
from krita import Extension,Krita,InfoObject
from PyQt5.QtCore import QTimer
from pathlib import Path
import json,traceback
class NativeExport(Extension):
 def setup(self):pass
 def createActions(self,window):
  self.action=window.createAction('has_native_export','HAS private native export')
  self.action.triggered.connect(self.run);QTimer.singleShot(1000,self.action.trigger)
 def run(self):
  result={'ok':False,'frames':0}
  try:
   app=Krita.instance();self.doc=app.openDocument('/input/source.kra');doc=self.doc
   if doc is None:raise RuntimeError('Krita could not open the reviewed source')
   doc.setBatchmode(True);app.activeWindow().addView(doc);doc.waitForDone()
   animated=Path('/tmp/has-animated').exists()
   start,end=(doc.fullClipRangeStartTime(),doc.fullClipRangeEndTime()) if animated else (doc.currentTime(),doc.currentTime())
   if start<0 or end<start or end-start>=240:raise RuntimeError('Native animation range exceeds its reviewed budget')
   options=InfoObject();options.setProperty('alpha',True);options.setProperty('compression',3)
   for index,frame in enumerate(range(start,end+1)):
    doc.setCurrentTime(frame);doc.refreshProjection();doc.waitForDone()
    if not doc.exportImage('/output/frame%04d.png'%index,options):raise RuntimeError('Krita could not export native frame%d'%frame)
    doc.waitForDone();result['frames']+=1;print('HAS_NATIVE_FRAME',index,flush=True)
   doc.setModified(False)
   if not doc.close():raise RuntimeError('Native document did not close cleanly')
   self.doc=None;result.update(ok=True,start=start,end_inclusive=end)
  except Exception:result['error']=traceback.format_exc()
  Path('/output/.native-result.json').write_text(json.dumps(result))
  QTimer.singleShot(1000,lambda:Krita.instance().action('file_quit').trigger())
Krita.instance().addExtension(NativeExport(Krita.instance()))
"""
plugins=Path('/tmp/data/krita/pykrita');(plugins/'has_native_export').mkdir(parents=True,exist_ok=True)
(plugins/'has_native_export/__init__.py').write_text(PLUGIN)
(plugins/'has_native_export.desktop').write_text('[Desktop Entry]\nType=Service\nServiceTypes=Krita/PythonPlugin\nX-KDE-Library=has_native_export\nName=HAS private native export\n')
(config/'kritarc').write_text('[General]\nmaxNumberOfThreads=2\nframeRenderingClones=1\n[python]\nenable_has_native_export=true\n')
if sys.argv[1]=='--export-sequence':Path('/tmp/has-animated').touch()
read_fd,write_fd=os.pipe()
server=subprocess.Popen(['Xvfb','-displayfd',str(write_fd),'-screen','0','1400x900x24','-nolisten','tcp','-ac'],pass_fds=(write_fd,))
os.close(write_fd)
proof={'format':'has_private_xvfb_1','ready':False,'child_started':False}
try:
    if not select.select([read_fd],[],[],20)[0]:raise RuntimeError('Private Xvfb did not become ready')
    display=os.read(read_fd,32).decode('ascii').strip()
    if not display.isdecimal() or server.poll() is not None:raise RuntimeError('Private Xvfb failed its readiness handshake')
    environment=os.environ.copy();environment['DISPLAY']=':'+display
    child=subprocess.Popen(['krita','--nosplash'],env=environment)
    proof.update(ready=True,child_started=True,display=':'+display,xvfb_pid=server.pid,child_pid=child.pid)
    Path('/output/.private-display.json').write_text(json.dumps(proof))
    code=child.wait();proof['child_exit']=code
    Path('/output/.private-display.json').write_text(json.dumps(proof))
finally:
    os.close(read_fd)
    server.terminate()
    try:server.wait(timeout=5)
    except subprocess.TimeoutExpired:server.kill();server.wait()
sys.exit(code)
'''

def mount(source,target,readonly=False):
    stream=io.StringIO();csv.writer(stream,lineterminator='').writerow(['type=bind','src='+str(source),'dst='+target,*(['readonly'] if readonly else [])]);return stream.getvalue()


def run_private(image,source,output,receipt_path,cancel_file=None,timeout=180,memory_mib=3072,animated=False):
    if not re.fullmatch(r'sha256:[0-9a-f]{64}',image):raise ValueError('Select an existing immutable Krita runtime image ID')
    if not .1<=timeout<=600 or type(memory_mib) is not int or not 256<=memory_mib<=4096:raise ValueError('Invalid private renderer budget')
    source=Path(source).resolve(strict=True);output=Path(output).resolve(strict=True);receipt_path=Path(receipt_path).absolute()
    if not source.is_file() or source.suffix.lower()!='.kra':raise ValueError('Choose a native KRA file')
    if source.is_relative_to(output) or any(output.iterdir()):raise ValueError('Private renderer needs an empty output folder separate from its source')
    if receipt_path.parent.resolve()!=output.parent:raise ValueError('Private renderer receipt must stay in its owned preparation folder')
    env=os.environ.copy()
    for key in ['DOCKER_HOST','DOCKER_CONTEXT','DOCKER_TLS','DOCKER_TLS_VERIFY','DOCKER_CERT_PATH']:env.pop(key,None)
    docker=['docker','--host=unix:///var/run/docker.sock'];token=uuid.uuid4().hex;name='has-krita-'+token
    receipt=dict(format='studio_private_krita_container_1',backend='docker-xvfb',image_id=image,container_name=name,container_started=False,container_removed=False,launcher_reaped=False,private_display=False,network_disabled=False,source_read_only=False,read_only_root=False,exit=None,cancelled=False,timed_out=False)
    process=None;container=None;started=time.monotonic()
    def write():
        temporary=receipt_path.with_suffix(receipt_path.suffix+'.tmp');temporary.write_text(json.dumps(receipt,indent=2)+'\n');os.replace(temporary,receipt_path)
    def command(args,limit=15,check=True):
        result=subprocess.run(docker+args,env=env,stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=limit)
        if check and result.returncode:raise RuntimeError((result.stderr or result.stdout).strip()[:2000])
        return result
    def inspect():
        r=command(['inspect','--format','{{json .}}',container or name],check=False)
        if r.returncode:
            if any(text in r.stderr.lower() for text in ['no such object:', 'no such container:']):return None
            raise RuntimeError('Cannot confirm private container state: '+r.stderr[:400])
        value=json.loads(r.stdout)
        if value['Config'].get('Labels',{}).get('org.has.native-job')!=token:raise RuntimeError('Private container ownership differs')
        return value
    def cleanup():
        value=inspect()
        if value is not None:command(['rm','-f',value['Id']])
        if inspect() is not None:raise RuntimeError('Private container was not removed')
        receipt['container_removed']=True
    try:
        if cancel_file and Path(cancel_file).exists():receipt.update(cancelled=True,exit=2);return receipt
        actual=command(['image','inspect','--format','{{.Id}}',image]).stdout.strip()
        if actual!=image:raise RuntimeError('Krita runtime image identity differs')
        args=['create','--pull=never','--name',name,'--label','org.has.native-job='+token,'--init','--network','none','--read-only','--user',f'{os.getuid()}:{os.getgid()}','--cap-drop','ALL','--security-opt','no-new-privileges','--memory',str(memory_mib)+'m','--cpus','2','--pids-limit','512','--tmpfs','/tmp:size=536870912']
        for key in ['HTTP_PROXY','HTTPS_PROXY','NO_PROXY','http_proxy','https_proxy','no_proxy']:args+=['-e',key+'=']
        # Krita otherwise sizes parallel frame clones from host CPU/RAM rather
        # than this container's two-CPU budget. Only owned temporary settings
        # are written; native documents never supply executable startup code.
        args+=['--mount',mount(source,'/input/source.kra',True),'--mount',mount(output,'/output'),image,'python3','-c',START_RENDERER,'--export-sequence' if animated else '--export']
        container=command(args).stdout.strip()
        if not re.fullmatch('[0-9a-f]{64}',container):raise RuntimeError('Private container creation returned no identity')
        receipt['container_id']=container
        value=inspect();host=value['HostConfig'];binds=[m for m in value['Mounts'] if m['Type']=='bind']
        if not (host['NetworkMode']=='none' and host['ReadonlyRootfs'] and host['Init'] and not host['Privileged']):raise RuntimeError('Private renderer isolation differs')
        if not ('ALL' in host['CapDrop'] and any(x.startswith('no-new-privileges') for x in host['SecurityOpt'])):raise RuntimeError('Private renderer capability isolation differs')
        if not (len(binds)==2 and any(m['Destination']=='/input/source.kra' and not m['RW'] for m in binds) and any(m['Destination']=='/output' and m['RW'] for m in binds)):raise RuntimeError('Private renderer mounts differ')
        receipt.update(private_display=True,network_disabled=True,source_read_only=True,read_only_root=True,memory_limit_requested_bytes=host['Memory'],init=True,render_threads_requested=2,frame_clones_requested=1)
        if cancel_file and Path(cancel_file).exists():receipt.update(cancelled=True,exit=2);return receipt
        process=subprocess.Popen(docker+['start','--attach',container],env=env,stdin=subprocess.DEVNULL)
        receipt['launcher_pid']=process.pid;write()
        while process.poll() is None:
            if not receipt['container_started']:
                value=inspect()
                if value and value['State']['Running']:receipt['container_started']=True;write()
            if cancel_file and Path(cancel_file).exists():receipt.update(cancelled=True,exit=2);break
            if time.monotonic()-started>timeout:receipt.update(timed_out=True,exit=2);break
            time.sleep(.05)
        if receipt['exit'] is None:
            value=inspect();receipt['exit']=int(value['State']['ExitCode']) if value and not value['State']['Running'] else process.returncode
        return receipt
    except BaseException as error:
        receipt.update(exit=1,error=str(error));raise
    finally:
        try:cleanup()
        except BaseException as error:
            receipt['cleanup_error']=str(error);receipt['exit']=1
        if process:
            try:process.wait(timeout=10)
            except subprocess.TimeoutExpired:process.kill();process.wait(timeout=5)
            receipt['launcher_reaped']=True
        proof=output/'.private-display.json'
        if proof.is_file() and proof.stat().st_size<4096:
            try:
                display=json.loads(proof.read_bytes())
                receipt['private_display_started']=display.get('format')=='has_private_xvfb_1' and display.get('ready') is True and display.get('child_started') is True and bool(re.fullmatch(r':[0-9]+',display.get('display','')))
            except (ValueError,OSError,TypeError):receipt['private_display_started']=False
        native_result=output/'.native-result.json'
        if receipt['exit']==0:
            try:
                native=json.loads(native_result.read_bytes()) if native_result.stat().st_size<65536 else {}
                if native.get('ok') is not True:raise RuntimeError(str(native.get('error','No native export result')))
                receipt['native_export']=native
            except (OSError,ValueError,RuntimeError) as error:receipt.update(exit=1,error='Native frame export failed: '+str(error))
        receipt['elapsed_seconds']=time.monotonic()-started;write()


def main():
    def interrupted(_number,_frame):raise InterruptedError("Private renderer interrupted; cleaning owned container")
    signal.signal(signal.SIGTERM,interrupted)
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--image',required=True);p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--receipt',type=Path,required=True);p.add_argument('--cancel-file',type=Path);p.add_argument('--timeout',type=float,default=180);p.add_argument('--memory-limit-mib',type=int,default=3072);p.add_argument('--animated',action='store_true');o=p.parse_args()
    receipt=run_private(o.image,o.source,o.output,o.receipt,o.cancel_file,o.timeout,o.memory_limit_mib,o.animated);return int(receipt['exit'])
if __name__=='__main__':raise SystemExit(main())
