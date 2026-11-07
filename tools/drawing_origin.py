"""Portable descriptive drawing ancestry, never an external asset reference."""
import json,math,re
try:from .drawing_limits import MAX_CELS
except ImportError:from drawing_limits import MAX_CELS
FIELDS={'format','kind','name','sha256','width','height','fps','range','visibility','fit','rate','at','duration'}
def integer(v,low,high):return type(v) in (int,float) and math.isfinite(v) and v==math.floor(v) and low<=v<=high
def text(v,limit):return isinstance(v,str) and 0<len(v)<=limit and not any(ord(c)<32 or ord(c)==127 or 0xd800<=ord(c)<=0xdfff for c in v)
def error(v):
    video=isinstance(v,dict) and v.get('format') in ('studio_drawing_origin_2','studio_drawing_origin_4') and v.get('kind')=='video'
    fields=(FIELDS-{'fps','range','visibility'})|{'source_rate','source_duration','chroma'} if video else FIELDS
    if not isinstance(v,dict) or set(v)!=fields:return 'Invalid drawing source history'
    if not video and (v['format'] not in ('studio_drawing_origin_1','studio_drawing_origin_3') or v['kind']!='krita'):return 'Unknown drawing source history'
    if not text(v['name'],200) or any(c in v['name'] for c in '/\\:') or not isinstance(v['sha256'],str) or re.fullmatch('[0-9a-f]{64}',v['sha256']) is None:return 'Invalid drawing source identity'
    if not integer(v['width'],1,32768) or not integer(v['height'],1,32768) or v['width']*v['height']>16777216:return 'Invalid original drawing dimensions'
    if video:
        for key,limit in [('source_rate',240),('source_duration',60)]:
            r=v[key]
            if not isinstance(r,list) or len(r)!=2 or any(not integer(n,1,1000000000) for n in r) or r[0]/r[1]>limit:return 'Invalid source video timing'
        c=v['chroma']
        if not isinstance(c,dict) or set(c)!={'enabled','color','similarity','blend'} or type(c['enabled']) is not bool or c['color'] not in ('00ff00','0000ff'):return 'Invalid chroma choices'
        for key,low in [('similarity',.01),('blend',0)]:
            if type(c[key]) not in (int,float) or not math.isfinite(c[key]) or not low<=c[key]<=1:return 'Invalid chroma choices'
    else:
        if not integer(v['fps'],0,1000):return 'Invalid original drawing timing'
        r=v['range']
        if not isinstance(r,list) or len(r) not in (0,2) or (r and (not integer(r[0],0,10000000) or not integer(r[1],r[0],10000000))):return 'Invalid original drawing range'
        visibility=v['visibility']
        if not isinstance(visibility,dict) or len(visibility)>128 or any(not text(k,128) or type(b) is not bool for k,b in visibility.items()):return 'Invalid original layer choices'
    f=v['fit']
    if not isinstance(f,list) or len(f)!=4 or not integer(f[0],1,1920) or not integer(f[1],1,1080) or not integer(f[2],0,1920-f[0]) or not integer(f[3],0,1080-f[1]):return 'Invalid drawing fit'
    r=v['rate']
    if not isinstance(r,list) or len(r)!=2 or not integer(r[0],1,120000) or not integer(r[1],1,1001) or r[0]/r[1]>120:return 'Invalid import rate'
    limit=7200 if v['format'] in ('studio_drawing_origin_3','studio_drawing_origin_4') else 240
    duration_limit=MAX_CELS if v['format']=='studio_drawing_origin_4' else 240
    if not integer(v['at'],0,limit-1) or not integer(v['duration'],1,duration_limit) or v['at']+v['duration']>limit:return 'Invalid original drawing placement'
    if len(json.dumps(v,ensure_ascii=False).encode())>32768:return 'Drawing source history exceeds its limit'
    return ''
