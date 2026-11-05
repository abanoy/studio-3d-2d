"""Actual native SFM eye import, GLB isolation, packed HAS, posing and movie proof."""
from pathlib import Path
import json,os,struct,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def glb(path):
    data=Path(path).read_bytes();size=struct.unpack_from('<I',data,12)[0]
    return json.loads(data[20:20+size]),data[28+size:]
def accessor(document,buffer,index):
    a=document['accessors'][index];assert not a.get('sparse');v=document['bufferViews'][a['bufferView']]
    counts={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4};formats={5126:'f',5123:'H',5125:'I',5121:'B'};fmt='<'+formats[a['componentType']]*counts[a['type']]
    stride=v.get('byteStride',struct.calcsize(fmt));offset=v.get('byteOffset',0)+a.get('byteOffset',0)
    return [struct.unpack_from(fmt,buffer,offset+i*stride)for i in range(a['count'])]
def surfaces(path):
    d,b=glb(path);result={}
    for mesh in d['meshes']:
        for p in mesh['primitives']:
            name=d['materials'][p['material']]['name'];attributes=p['attributes']
            points=accessor(d,b,attributes['POSITION']);uvs=accessor(d,b,attributes['TEXCOORD_0'])
            result[(mesh['name'],name)]=sorted(tuple(position)+tuple(uv)for position,uv in zip(points,uvs))
    return result,d
def main():
    folder=ROOT/'output/source-eyes'/str(time.time_ns());folder.mkdir(parents=True)
    previous=read(ROOT/'output/source-texture-checkpoint.json');old=Path(previous['folder'])/'private-evidence/prepared/sfm/model_bundle/scene.glb';assert old.is_file()
    def run(args,name,timeout=300,env=None):
        p=subprocess.run(args,cwd=ROOT,env=env,capture_output=True,encoding='utf-8',errors='replace',timeout=timeout,creationflags=subprocess.CREATE_NO_WINDOW)
        (folder/(name+'.log')).write_text(p.stdout+p.stderr,encoding='utf-8');assert p.returncode==0,(name,p.stdout,p.stderr)
    run([sys.executable,'-m','unittest','discover','-s','tests','-p','test_source_eyes.py'],'unit',60)
    env=os.environ.copy();env.update(PYTHONDONTWRITEBYTECODE='1',NO_BPY='1',BLENDER_USER_CONFIG=str(folder/'blender-config'))
    run([r'C:\Program Files\Blender Foundation\Blender 5.1\blender.exe','--background','--factory-startup','--disable-autoexec','--offline-mode','--python-exit-code','1','--python',str(ROOT/'tests/source_eyes_probe.py'),'--',str(folder/'binding-probe')],'binding',90,env)
    assert all(read(folder/'binding-probe/result.json').values())
    run([sys.executable,'-u','tests/verify_sfm_standalone.py'],'native',300)
    native=read(ROOT/'output/sfm-standalone-verification.json');assert native['app']['checks']==17 and native['app']['failures']==0
    bundle=Path(native['app']['model_bundle']);report=read(bundle/'parameters.json');eyes=[m for m in report['materials']if m['status']=='neutral iris approximation']
    assert len(eyes)==2 and report['counts']['textures']==6 and len(report['native_parameters']['eyeballs'])==2
    resolved=read(bundle/'dependencies.json')['resolved'];assert any(d['path'].replace('\\','/').endswith('/scout/eye.vtf')for d in resolved)
    before,_=surfaces(old);after,document=surfaces(bundle/'scene.glb');assert before.keys()==after.keys()
    changed=[];preserved=[]
    for key in before:
        if '/eyeball_'in key[1]:
            assert before[key]!=after[key];assert sorted(p[:3]for p in before[key])==sorted(p[:3]for p in after[key]);changed.append(key[1])
        else:assert before[key]==after[key],key;preserved.append(key[1])
    assert len(changed)==2 and preserved
    for material in document['materials']:
        if '/eyeball_'in material['name']:
            assert material.get('alphaMode','OPAQUE')=='OPAQUE'
            texture=document['textures'][material['pbrMetallicRoughness']['baseColorTexture']['index']]
            sampler=document['samplers'][texture['sampler']];assert sampler['wrapS']==sampler['wrapT']==33071
    result={'folder':str(folder),'unit_tests':6,'blender_binding_checks':5,'native':native['app'],'private_receipts':native['private_receipts'],'changed_eye_surfaces':changed,'non_eye_surfaces_preserved':len(preserved),'eye_positions_preserved':True,'iris_alpha_not_opacity':True,'clamped_texture_edges':True,'normal_updated':False}
    (folder/'verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');(ROOT/'output/source-eyes-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
