"""Bounded extended parent timing with explicit project schema8."""
import math
LEGACY_FRAMES=240
MAX_FRAMES=7200
MAX_SECONDS=60
LEGACY_PLACEMENT=1000240
MAX_PLACEMENT=1000000+MAX_FRAMES

def integer(value,low,high):return type(value) in (int,float) and math.isfinite(value) and value==math.floor(value) and low<=value<=high

def video_error(video):
    if not isinstance(video,dict):return 'Missing project timing'
    n,d=video.get('fps_num'),video.get('fps_den')
    if not integer(n,1,120000) or not integer(d,1,1001) or n>120*d:return 'Invalid project frame rate'
    count=video.get('duration_frames')
    if not integer(count,1,MAX_FRAMES):return 'Invalid extended scene length'
    if count>LEGACY_FRAMES and count*d>n*MAX_SECONDS:return 'Longer scenes support up to 60 seconds and 7200 frames'
    return ''

def origin_extended(layers):return isinstance(layers,list) and any(isinstance(v,dict) and isinstance(v.get('origin'),dict) and v['origin'].get('format') in ('studio_drawing_origin_3','studio_drawing_origin_4') for v in layers)
def extended_keys(clips):return isinstance(clips,list) and any(isinstance(v,dict) and isinstance(v.get('keys'),list) and any(isinstance(k,dict) and type(k.get('frame')) in (int,float) and k['frame']>LEGACY_PLACEMENT for k in v['keys']) for v in clips)
def required(document):
    video=document.get('video',{})
    if isinstance(video,dict) and type(video.get('duration_frames')) in (int,float) and video['duration_frames']>LEGACY_FRAMES:return True
    if origin_extended(document.get('layers',[])):return True
    graph=document.get('sequence_graph',{})
    if isinstance(graph,dict):
        if extended_keys(graph.get('clips',[])):return True
        if isinstance(graph.get('assets'),list):
            for asset in graph['assets']:
                if not isinstance(asset,dict):continue
                scene=asset.get('scene',{})
                if extended_keys(asset.get('clips',[])) or isinstance(scene,dict) and (scene.get('schema_version')==8 or origin_extended(scene.get('layers',[]))):return True
    return False

def unwrap(value):
    version=value.get('timing_content_schema_version')
    if not integer(version,3,7):return None,'Invalid extended-timing content schema'
    why=video_error(value.get('video'))
    if why:return None,why
    base=dict(value);base['schema_version']=int(base.pop('timing_content_schema_version'));return base,''

def child_schema(scene):
    if scene.get('schema_version')==8:
        base,why=unwrap(scene)
        return -1 if why else base['schema_version']
    value=scene.get('schema_version')
    return int(value) if integer(value,1,7) else -1
