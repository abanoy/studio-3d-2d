"""Run only in isolated offline Blender. Compare the production boundary to PNG loading."""
from pathlib import Path
import bpy,importlib.util,json,struct,sys,zlib
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from source_texture import blender_rgba
folder=Path(sys.argv[sys.argv.index('--')+1]);folder.mkdir(parents=True,exist_ok=True)
base=ROOT/'output/dependencies/sourceio-fe24260b97ac03b899d9b5d4f0fd7b34772f3647/library/utils/pylib'
spec=importlib.util.spec_from_file_location('has_orientation_pylib',base/'__init__.py',submodule_search_locations=[str(base)])
module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
cases=[]
for w,h,colors in [(2,2,[(255,0,0,255),(0,255,0,255),(0,0,255,255),(255,255,0,255)]),
                   (2,3,[(128,64,192,255),(11,200,70,128),(255,128,0,255),(64,32,16,200),(0,255,255,255),(255,0,255,127)]),
                   (3,1,[(255,0,0,255),(0,255,0,255),(0,0,255,255)])]:
    raw=bytes(channel for color in colors for channel in color);header=bytearray(80);header[:4]=b'VTF\0'
    struct.pack_into('<III',header,4,7,2,80);struct.pack_into('<HH',header,16,w,h);struct.pack_into('<H',header,24,1);struct.pack_into('<f',header,48,1);struct.pack_into('<I',header,52,0);header[56]=1;struct.pack_into('<I',header,57,0xffffffff);struct.pack_into('<H',header,63,1)
    vtf=bytes(header)+raw;(folder/f'authored-{w}x{h}.vtf').write_bytes(vtf)
    pixels,width,height,is_float=module.vtf.load_vtf_texture(vtf)
    assert(width,height,is_float)==(w,h,False)and bytes(pixels)==raw
    scanlines=b''.join(b'\0'+raw[y*w*4:(y+1)*w*4]for y in range(h))
    png=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(scanlines))+chunk(b'IEND',b'')
    reference=folder/f'authored-{w}x{h}.png';reference.write_bytes(png)
    rows=np.frombuffer(pixels,dtype=np.uint8).reshape(h,w,4).astype(np.float32)/255
    file=bpy.data.images.load(str(reference));file.alpha_mode='CHANNEL_PACKED'
    actual=bpy.data.images.new(f'production-{w}x{h}',width=w,height=h,alpha=True);actual.alpha_mode='CHANNEL_PACKED';actual.pixels.foreach_set(blender_rgba(rows,w,h))
    delta=max(abs(a-b)for a,b in zip(file.pixels[:],actual.pixels[:]));assert delta<1e-6,(w,h,delta,list(file.pixels[:]),list(actual.pixels[:]))
    cases.append({'width':w,'height':h,'decoder_matches_authored':True,'max_pixel_delta':delta})
try:blender_rgba(np.zeros((2,2,3),dtype=np.float32),2,2)
except ValueError:pass
else:raise AssertionError('Malformed channel count accepted')
result={'cases':cases,'invalid_channels_refused':True}
(folder/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print('SOURCE_TEXTURE_PROBE '+json.dumps(result))
