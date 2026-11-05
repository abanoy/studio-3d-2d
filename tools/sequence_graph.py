"""Editable, project-local scene sequences. Pure metadata; never resolve sources."""
import math
try:from . import extended_timing as extended
except ImportError:import extended_timing as extended
import re

FORMAT='studio_sequences_1'
SHADOW_FORMAT='studio_sequences_2'
MASK_FORMAT='studio_sequences_3'
CLIP_FIELDS={'id','asset_id','start','duration','source_in','time_in','key_in','loop','visible','muted','gain_db','keys'}
KEY_FIELDS={'frame','offset','scale','rotation','opacity','interpolation'}


def number(v,lo,hi):
    return type(v) in (int,float) and math.isfinite(v) and lo<=v<=hi


def integer(v,lo,hi):
    return number(v,lo,hi) and v==math.floor(v)


def identity(v):
    return isinstance(v,str) and re.fullmatch(r'[A-Za-z0-9_-]{1,128}',v) is not None


def error(graph,root):
    if not isinstance(graph,dict) or set(graph)!={'format','assets','clips'} or graph['format'] not in (FORMAT,SHADOW_FORMAT,MASK_FORMAT):
        return 'Unknown editable sequence graph'
    assets=graph['assets']
    if not isinstance(assets,list) or not 1<=len(assets)<=4:return 'Expected 1–4 editable sequence assets'
    if not isinstance(root,dict) or not isinstance(root.get('video'),dict):return 'Missing parent sequence timing'
    rate=root['video'];index={};documents=[root]
    for asset in assets:
        if not isinstance(asset,dict) or set(asset)!={'id','name','scene','clips'} or not identity(asset['id']) or asset['id'] in index:return 'Invalid or duplicate sequence identity'
        name=asset['name']
        if not isinstance(name,str) or not 1<=len(name)<=80 or any(ord(c)<32 or ord(c)==127 or 0xd800<=ord(c)<=0xdfff for c in name):return 'Invalid sequence name'
        scene=asset['scene']
        if not isinstance(scene,dict) or extended.child_schema(scene) not in (4,5) or any(k in scene for k in ('sequence_graph','scene','model')):return 'Sequence scenes require a world document without another embedded graph'
        index[asset['id']]=asset;documents.append(scene)
    cels=sounds=objects=effects=0
    for position,scene in enumerate(documents):
        video=scene.get('video')
        if not isinstance(video,dict) or extended.video_error(video) or position>0 and not integer(video.get('duration_frames'),1,240):return 'Invalid parent/local sequence duration'
        for key in ('width','height','fps_num','fps_den'):
            if video.get(key)!=rate.get(key):return 'Sequences must share canvas size and frame rate'
        if video.get('width')!=1920 or video.get('height')!=1080 or not integer(video.get('fps_num'),1,120000) or not integer(video.get('fps_den'),1,1001) or video['fps_num']/video['fps_den']>120:return 'Invalid sequence canvas/rate'
        layers=scene.get('layers');world=scene.get('world');audio=scene.get('audio',{})
        if not isinstance(layers,list) or len(layers)>4 or not isinstance(world,dict) or not isinstance(world.get('objects'),list) or not isinstance(world.get('effects',[]),list) or not isinstance(audio,dict):return 'Invalid sequence scene tracks'
        for layer in layers:
            if not isinstance(layer,dict) or not isinstance(layer.get('cels'),list):return 'Invalid sequence drawing track'
            cels+=len(layer['cels'])
        rows=audio.get('clips') if 'clips' in audio else [audio] if audio else []
        if not isinstance(rows,list):return 'Invalid sequence audio tracks'
        sounds+=len(rows);objects+=len(world['objects']);effects+=len(world.get('effects',[]))
    if cels>32 or sounds>16 or objects>64 or effects>16:return 'Sequences exceed the shared drawing/audio/world resource budget'
    ids=set();total=0
    for owner,clips in [('',graph['clips'])]+[(a['id'],a['clips']) for a in assets]:
        if not isinstance(clips,list):return 'Invalid sequence clips'
        parent=root if not owner else index[owner]['scene']
        total+=len(clips)
        if total>8:return 'At most8 sequence clips per project'
        for clip in clips:
            expected=CLIP_FIELDS|({'shadow'} if graph['format']!=FORMAT else set())|({'mask'} if graph['format']==MASK_FORMAT else set())
            if not isinstance(clip,dict) or set(clip)!=expected or not identity(clip['id']) or clip['id'] in ids or not isinstance(clip['asset_id'],str) or clip['asset_id'] not in index:return 'Invalid sequence clip identity or missing asset'
            if graph['format']!=FORMAT:
                why=shadow_error(clip['shadow'])
                if why:return why
            if graph['format']==MASK_FORMAT:
                why=mask_error(clip['mask'])
                if why:return why
            ids.add(clip['id']);child=index[clip['asset_id']]['scene']['video']
            if not integer(clip['start'],0,parent['video']['duration_frames']-1) or not integer(clip['duration'],1,parent['video']['duration_frames']-clip['start']) or not integer(clip['source_in'],0,child['duration_frames']-1):return 'Sequence clip exceeds its parent/local range'
            if not integer(clip['time_in'],0,1000000) or not integer(clip['key_in'],0,1000000):return 'Invalid sequence source window'
            if any(type(clip[k]) is not bool for k in ('loop','visible','muted')) or not number(clip['gain_db'],-60,12):return 'Invalid sequence clip visibility/audio'
            if not clip['loop'] and clip['source_in']+clip['time_in']+clip['duration']>child['duration_frames']:return 'Non-looping sequence exceeds its source range'
            keys=clip['keys'];previous=-1
            if not isinstance(keys,list) or not 1<=len(keys)<=32:return 'Expected 1–32 sequence placement keys'
            for key in keys:
                if not isinstance(key,dict) or set(key)!=KEY_FIELDS or not integer(key['frame'],0,extended.MAX_PLACEMENT) or key['frame']<=previous or (previous<0 and key['frame']!=0):return 'Invalid sequence placement key timing'
                if not isinstance(key['offset'],list) or len(key['offset'])!=2 or any(not number(v,-19200,19200) for v in key['offset']) or not number(key['scale'],.01,8) or not number(key['rotation'],-36000,36000) or not number(key['opacity'],0,1) or key['interpolation'] not in ('linear','hold','ease'):return 'Invalid sequence placement key'
                previous=key['frame']
    context=root.get('editor',{})
    if isinstance(context,dict) and 'sequence_editor' in context:
        value=context['sequence_editor']
        if not isinstance(value,dict) or set(value)!={'format','asset_id','frame'} or value['format']!='studio_sequence_editor_1' or not isinstance(value['asset_id'],str) or value['asset_id'] not in index or not integer(value['frame'],0,index[value['asset_id']]['scene']['video']['duration_frames']):return 'Invalid sequence editor context'
    def visit(owner,path):
        if owner in path:return 'Cyclic editable sequence reference'
        if len(path)>=4:return 'Editable sequence nesting exceeds4levels'
        for clip in index[owner]['clips']:
            why=visit(clip['asset_id'],path+[owner])
            if why:return why
        return ''
    for asset in assets:
        why=visit(asset['id'],[])
        if why:return why
    return ''


def shadow_error(value):
    if not isinstance(value,dict):return 'Invalid sequence shadow'
    if not value:return ''
    if set(value)!={'offset','color','softness'} or not isinstance(value['offset'],list) or len(value['offset'])!=2 or not isinstance(value['color'],list) or len(value['color'])!=4 or not number(value['softness'],0,32):return 'Invalid sequence shadow'
    if any(not number(n,-2048,2048) for n in value['offset']):return 'Sequence shadow offset exceeds2048pixels'
    if any(not number(n,0,1) for n in value['color']):return 'Invalid sequence shadow color'
    return ''


def mask_error(value):
    if not isinstance(value,dict):return 'Invalid sequence picture mask'
    if not value:return ''
    if set(value)!={'rect','invert'} or not isinstance(value['rect'],list) or len(value['rect'])!=4 or type(value['invert']) is not bool:return 'Invalid sequence picture mask'
    r=value['rect']
    if not integer(r[0],0,1919) or not integer(r[1],0,1079) or not integer(r[2],1,1920) or not integer(r[3],1,1080) or r[0]+r[2]>1920 or r[1]+r[3]>1080:return 'Picture mask must be a whole-pixel rectangle inside the child canvas'
    return ''


def local_frame(clip,frame,duration):
    offset=frame-clip['start']
    if offset<0 or offset>=clip['duration']:return -1
    value=clip['source_in']+clip['time_in']+offset
    return value%duration if clip['loop'] else value if value<duration else -1
