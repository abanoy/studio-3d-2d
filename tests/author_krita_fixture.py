"""Author original forty-frame transparent artwork through the real Krita API.

Uses only this repository's trusted fixture plugin, never document-supplied code.
The output directory must not exist. No host desktop or existing Krita is used.
"""
from pathlib import Path
import argparse,json,os,re,struct,subprocess,sys,tempfile,uuid,zlib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.private_krita_container import mount


def png(frame):
    pixels=bytearray(256*144*4)
    for y in range(48,80):
        for x in range(20+frame*3,52+frame*3):pixels[(y*256+x)*4:(y*256+x+1)*4]=bytes([220,60,30,160])
    def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
    rows=b''.join(b'\0'+pixels[y*1024:(y+1)*1024] for y in range(144))
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',256,144,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(rows))+chunk(b'IEND',b'')


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--image',required=True);parser.add_argument('--output',type=Path,required=True);options=parser.parse_args()
    if not re.fullmatch('sha256:[0-9a-f]{64}',options.image):raise ValueError('Use a local immutable Krita image ID')
    output=options.output.resolve();output.mkdir(parents=True,exist_ok=False)
    env=os.environ.copy()
    for key in ['DOCKER_HOST','DOCKER_CONTEXT','DOCKER_TLS','DOCKER_TLS_VERIFY','DOCKER_CERT_PATH']:env.pop(key,None)
    docker=['docker','--host=unix:///var/run/docker.sock'];token=uuid.uuid4().hex;name='has-krita-author-'+token
    startup="from pathlib import Path; import shutil,os; p=Path('/tmp/data/krita/pykrita'); p.parent.mkdir(parents=True,exist_ok=True); shutil.copytree('/fixture-plugin',p); c=Path('/tmp/config'); c.mkdir(parents=True,exist_ok=True); (c/'kritarc').write_text('[python]\\nenable_has_fixture=true\\n'); os.execvp('xvfb-run',['xvfb-run','-a','-s','-screen 0 1400x900x24 -nolisten tcp','krita','--nosplash'])"
    def command(args,**kwargs):return subprocess.run(docker+args,env=env,stdin=subprocess.DEVNULL,check=True,**kwargs)
    with tempfile.TemporaryDirectory(prefix='has-krita-input-',dir=output.parent) as temporary:
        inputs=Path(temporary)
        for frame in range(40):(inputs/f'frame{frame:03d}.png').write_bytes(png(frame))
        try:
            args=['create','--pull=never','--name',name,'--label','org.has.fixture-author='+token,'--init','--network','none','--read-only','--user',f'{os.getuid()}:{os.getgid()}','--cap-drop','ALL','--security-opt','no-new-privileges','--memory','3g','--cpus','2','--pids-limit','512','--tmpfs','/tmp:size=536870912']
            for key in ['HTTP_PROXY','HTTPS_PROXY','NO_PROXY','http_proxy','https_proxy','no_proxy']:args+=['-e',key+'=']
            for source,target,readonly in [(inputs,'/fixture-input',True),(Path(__file__).with_name('krita_fixture'),'/fixture-plugin',True),(output,'/output',False)]:args+=['--mount',mount(source,target,readonly)]
            args += [options.image,'python3','-c',startup]
            command(args,stdout=subprocess.PIPE,text=True,timeout=30)
            command(['start','--attach',name],timeout=120)
            state=json.loads(command(['inspect','--format','{{json .}}',name],stdout=subprocess.PIPE,text=True,timeout=15).stdout)
            if state['State']['ExitCode']!=0 or not (output/'fixture.json').is_file() or (output/'fixture-error.txt').exists():raise RuntimeError('Native fixture authoring failed; inspect owned output')
        finally:
            result=subprocess.run(docker+['inspect','--format','{{json .Config.Labels}}',name],env=env,capture_output=True,text=True,timeout=15)
            if result.returncode==0:
                if json.loads(result.stdout).get('org.has.fixture-author')!=token:raise RuntimeError('Fixture container ownership differs')
                command(['rm','-f',name],stdout=subprocess.DEVNULL,timeout=20)
    print(json.dumps({'source':str(output/'Original animation.kra'),'frames':40,'native_authoring':True}))

if __name__=='__main__':main()
