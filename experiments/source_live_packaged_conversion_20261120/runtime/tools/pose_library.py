"""HAS authored body-pose metadata. No external asset resolution or retargeting."""
import base64,binascii,json,math,re,struct,zlib
FORMAT='studio_body_pose_library_1';FIELD='body_pose_library';MAX_BYTES=192*1024
def text(v,limit):return isinstance(v,str) and 0<len(v)<=limit and not any(ord(c)<32 or ord(c)==127 or 0xd800<=ord(c)<=0xdfff for c in v)
def numbers(v,n):return isinstance(v,list) and len(v)==n and all(type(x) in (int,float) and math.isfinite(x) and abs(x)<=100000 for x in v)
def thumbnail(v):
    if not isinstance(v,str) or not 0<len(v)<=32768:return False
    try:b=base64.b64decode(v,validate=True)
    except (ValueError,binascii.Error):return False
    if not 33<=len(b)<=24576 or base64.b64encode(b).decode()!=v or b[:8]!=b'\x89PNG\r\n\x1a\n' or b[12:16]!=b'IHDR' or struct.unpack('>II',b[16:24])!=(96,54) or b[24]!=8 or b[25] not in (2,6) or b[26:29]!=b'\0\0\0':return False
    at=8;payload=bytearray();end=False
    while at<len(b):
        if at+12>len(b):return False
        size=struct.unpack_from('>I',b,at)[0];kind=b[at+4:at+8];finish=at+12+size
        if finish>len(b) or zlib.crc32(b[at+4:at+8+size])&0xffffffff!=struct.unpack_from('>I',b,at+8+size)[0]:return False
        if kind==b'IDAT':payload.extend(b[at+8:at+8+size])
        if kind==b'IEND':end=finish==len(b);break
        at=finish
    if not end:return False
    width=96*(4 if b[25]==6 else 3)+1;maximum=54*width
    try:
        d=zlib.decompressobj();raw=d.decompress(payload,maximum+1)
        return d.eof and not d.unused_data and len(raw)==maximum and all(raw[y*width]<=4 for y in range(54))
    except zlib.error:return False
def error(v):
    if not isinstance(v,dict) or set(v)!= {'format','sha256','bone_ids','entries'} or v['format']!=FORMAT:return 'Invalid body-pose library format'
    if not isinstance(v['sha256'],str) or re.fullmatch('[0-9a-f]{64}',v['sha256']) is None:return 'Invalid body-pose source identity'
    bones=v['bone_ids']
    if not isinstance(bones,list) or not 1<=len(bones)<=512 or any(not text(x,512) or x=='@root' for x in bones) or len(set(bones))!=len(bones):return 'Invalid body-pose rig bindings'
    entries=v['entries']
    if not isinstance(entries,list) or len(entries)>16:return 'Body-pose library supports sixteen poses'
    ids=set();names=set()
    for entry in entries:
        if not isinstance(entry,dict) or set(entry)!= {'id','name','pose','thumbnail_png'} or not text(entry['id'],128) or entry['id'] in ids or not text(entry['name'],64) or entry['name'].lower() in names:return 'Invalid or duplicate body pose'
        ids.add(entry['id']);names.add(entry['name'].lower());pose=entry['pose']
        if not isinstance(pose,dict) or len(pose)>512:return 'Invalid saved body-pose transforms'
        for key,t in pose.items():
            if key not in bones or not isinstance(t,dict) or set(t)!= {'position','rotation_xyzw'} or not numbers(t['position'],3) or not numbers(t['rotation_xyzw'],4) or sum(x*x for x in t['rotation_xyzw'])<=.000001:return 'Invalid saved body-pose transform/binding'
        if not thumbnail(entry['thumbnail_png']):return 'Invalid saved body-pose thumbnail'
    if len(json.dumps(v,ensure_ascii=False,separators=(',',':')).encode())>MAX_BYTES:return 'Body-pose library exceeds192KiB'
    return ''
