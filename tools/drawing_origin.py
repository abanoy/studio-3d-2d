"""Portable descriptive drawing ancestry, never an external asset reference."""
import json,math,re
FIELDS={'format','kind','name','sha256','width','height','fps','range','visibility','fit','rate','at','duration'}
def integer(v,low,high):return type(v) in (int,float) and math.isfinite(v) and v==math.floor(v) and low<=v<=high
def text(v,limit):return isinstance(v,str) and 0<len(v)<=limit and not any(ord(c)<32 or ord(c)==127 or 0xd800<=ord(c)<=0xdfff for c in v)
def error(v):
    if not isinstance(v,dict) or set(v)!=FIELDS:return 'Invalid drawing source history'
    if v['format']!='studio_drawing_origin_1' or v['kind']!='krita':return 'Unknown drawing source history'
    if not text(v['name'],200) or any(c in v['name'] for c in '/\\:') or not isinstance(v['sha256'],str) or re.fullmatch('[0-9a-f]{64}',v['sha256']) is None:return 'Invalid drawing source identity'
    if not integer(v['width'],1,32768) or not integer(v['height'],1,32768) or v['width']*v['height']>16777216 or not integer(v['fps'],0,1000):return 'Invalid original drawing dimensions/timing'
    r=v['range']
    if not isinstance(r,list) or len(r) not in (0,2) or (r and (not integer(r[0],0,10000000) or not integer(r[1],r[0],10000000))):return 'Invalid original drawing range'
    visibility=v['visibility']
    if not isinstance(visibility,dict) or len(visibility)>128 or any(not text(k,128) or type(b) is not bool for k,b in visibility.items()):return 'Invalid original layer choices'
    f=v['fit']
    if not isinstance(f,list) or len(f)!=4 or not integer(f[0],1,1920) or not integer(f[1],1,1080) or not integer(f[2],0,1920-f[0]) or not integer(f[3],0,1080-f[1]):return 'Invalid drawing fit'
    r=v['rate']
    if not isinstance(r,list) or len(r)!=2 or not integer(r[0],1,120000) or not integer(r[1],1,1001) or r[0]/r[1]>120:return 'Invalid import rate'
    if not integer(v['at'],0,239) or not integer(v['duration'],1,240) or v['at']+v['duration']>240:return 'Invalid original drawing placement'
    if len(json.dumps(v,ensure_ascii=False).encode())>32768:return 'Drawing source history exceeds its limit'
    return ''
