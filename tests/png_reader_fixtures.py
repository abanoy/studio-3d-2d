"""Original PNG encodings with an independent mathematical straight-RGBA oracle."""
from pathlib import Path
import hashlib,json,struct,zlib

def make_fixtures(folder):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    def chunk(kind,data):return struct.pack('!I',len(data))+kind+data+struct.pack('!I',zlib.crc32(kind+data)&0xffffffff)
    def write(name,w,h,depth,color,raw,extra=(),interlace=0):
     data=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!2I5B',w,h,depth,color,0,0,interlace))+b''.join(chunk(k,v) for k,v in extra)+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b'');(folder/name).write_bytes(data)
    def packed(values,depth):
     value=0;bits=0;out=bytearray()
     for n in values:
      value=(value<<depth)|n;bits+=depth
      if bits==8:out.append(value);value=bits=0
     if bits:out.append(value<<(8-bits))
     return bytes(out)
    for depth in [1,2,4,8,16]:
     rows=[]
     for y in range(3):
      values=[(x+y)%2*((1<<depth)-1) for x in range(4)]
      rows.append(b'\0'+(b''.join(struct.pack('!H',n) for n in values) if depth==16 else packed(values,depth)))
     write(f'gray{depth}.png',4,3,depth,0,b''.join(rows),[(b'tRNS',struct.pack('!H',0))])
    for depth in [1,2,4,8]:
     palette=bytes([220,30,10,20,180,80]);raw=b''.join(b'\0'+packed([(x+y)%2 for x in range(4)],depth) for y in range(3))
     write(f'palette{depth}.png',4,3,depth,3,raw,[(b'PLTE',palette),(b'tRNS',bytes([0,128]))])
    for depth in [8,16]:
     for color,channels in [(2,3),(4,2),(6,4)]:
      raw=b''.join(b'\0'+b''.join(bytes([(x*71+y*23+c*53)%256]) if depth==8 else struct.pack('!H',((x*71+y*23+c*53)%256)*257) for x in range(4) for c in range(channels)) for y in range(3))
      write(f'color{color}-depth{depth}.png',4,3,depth,color,raw,[(b'gAMA',struct.pack('!I',45455)),(b'sRGB',b'\0'),(b'tEXt',b'note\0original generated fixture')])
    w,h=8,7;raw=b''
    for x0,y0,dx,dy in [(0,0,8,8),(4,0,8,8),(0,4,4,8),(2,0,4,4),(0,2,2,4),(1,0,2,2),(0,1,1,2)]:
     xs=list(range(x0,w,dx))
     if xs:
      for y in range(y0,h,dy):raw+=b'\0'+b''.join(bytes((x*17,y*23,(x+y)*17,128 if (x+y)%2 else 0)) for x in xs)
    write('interlaced.png',w,h,8,6,raw,interlace=1)
    gold={}
    for path in sorted(folder.glob('*.png')):
     name=path.name;w,h=(8,7) if name=='interlaced.png' else (4,3);rgba=bytearray()
     for y in range(h):
      for x in range(w):
       if name.startswith('gray'):pixel=(255,255,255,255) if (x+y)%2 else (0,0,0,0)
       elif name.startswith('palette'):pixel=(20,180,80,128) if (x+y)%2 else (220,30,10,0)
       elif name=='interlaced.png':pixel=(x*17,y*23,(x+y)*17,128 if (x+y)%2 else 0)
       else:
        color=int(name[5]);n=lambda c:(x*71+y*23+c*53)%256
        pixel=(n(0),n(1),n(2),255) if color==2 else (n(0),n(0),n(0),n(1)) if color==4 else (n(0),n(1),n(2),n(3))
       rgba.extend(pixel)
     gold[name]=dict(width=w,height=h,pixel_sha256=hashlib.sha256(rgba).hexdigest(),source_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    (folder/'expected.json').write_text(json.dumps(gold,indent=2),encoding='utf-8')
    return gold
