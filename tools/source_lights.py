"""Bounded static Source entity lights; no entity programs, baked maps or photometry claim."""
import math
import json
MAX_LIGHTS=64
MAX_WARNING_EXAMPLES=32
MAX_WARNING_CHARS=800
MAX_WARNING_BYTES=32*1024
SUPPORTED={'light':'POINT','light_spot':'SPOT','light_environment':'SUN'}

def numbers(value,count,label):
    if not isinstance(value,str) or len(value)>256:raise ValueError('Invalid Source light '+label)
    try:items=[float(x) for x in value.split()]
    except ValueError:raise ValueError('Invalid Source light '+label) from None
    if len(items)!=count or any(not math.isfinite(x) or abs(x)>1e9 for x in items):raise ValueError('Invalid Source light '+label)
    return items

def scalar(entity,key,default):return numbers(str(entity.get(key,default)),1,key)[0]
def linear(value):
    value=value/255
    return value/12.92 if value<=.04045 else ((value+.055)/1.055)**2.4


def _entity_light(entity,kind,scale):
    name=str(entity.get('targetname',kind))[:160]
    flags=scalar(entity,'spawnflags',0);style=scalar(entity,'style',0)
    if not flags.is_integer() or not 0<=flags<=4294967295 or not style.is_integer() or not 0<=style<=255:raise ValueError('Invalid Source light flags/style: '+name)
    if int(flags)&1:
        return None, name+': starts-off light retained in entities.json; not enabled in the imported scene.', 'starts_off'
    if style!=0:
        return None, name+': animated light style is unsupported; retained in entities.json.', 'animated_style'
    rgba=numbers(entity.get('_light','255 255 255 200'),4,'color/brightness')
    if any(not 0<=v<=255 for v in rgba[:3]) or not 0<=rgba[3]<=1000000:raise ValueError('Source light color or brightness exceeds bounds: '+name)
    origin=numbers(entity.get('origin','0 0 0'),3,'origin')
    angles=numbers(entity.get('angles','0 0 0'),3,'angles')
    # Source light pitch is negative down; entity-angle pitch is positive down.
    pitch=scalar(entity,'pitch',-angles[0]);yaw=angles[1]
    p,y=math.radians(pitch),math.radians(yaw)
    row={'name':name,'source_class':kind,'type':SUPPORTED[kind],
         'position':[x*scale for x in origin],
         'direction':[math.cos(p)*math.cos(y),math.cos(p)*math.sin(y),math.sin(p)],
         'color':[linear(v) for v in rgba[:3]],'source_brightness':rgba[3],
         'energy':rgba[3]/200 if kind=='light_environment' else rgba[3]*scale*scale*100}
    if kind=='light_spot':
        outer=scalar(entity,'_cone',45);inner=scalar(entity,'_inner_cone',30)
        if not 0<outer<=90 or not 0<=inner<outer:raise ValueError('Invalid Source spotlight cone: '+name)
        row.update(spot_size=math.radians(outer*2),spot_blend=1-inner/outer)
    return row, None, None

def plan(entities,scale,*,optional_omissions=False,remaining_budget=MAX_LIGHTS):
    """Strict default; BSP may explicitly omit optional unsupported lighting only.

    Malformed inventory/unit scale remain fatal. Never clamp/reinterpret a source
    light, run entity programs, or raise the global64-light budget.
    """
    if not isinstance(entities,list) or len(entities)>100000:raise ValueError('Invalid Source entity inventory')
    if not isinstance(scale,(int,float)) or isinstance(scale,bool) or not math.isfinite(scale) or not .0001<=scale<=10000:raise ValueError('Invalid Source light unit scale')
    if type(optional_omissions) is not bool:raise ValueError('Invalid optional Source light policy')
    if type(remaining_budget) is not int or not 0<=remaining_budget<=MAX_LIGHTS:raise ValueError('Invalid Source light remaining budget')
    result=[];warnings=[]
    counts={'format':'has_optional_source_map_light_omissions_1','policy':'omit_optional_lighting_preserve_geometry_and_raw_entities',
            'light_entities':0,'created':0,'invalid':0,'budget':0,'starts_off':0,'animated_style':0,'unsupported_type':0,
            'global_limit':MAX_LIGHTS,'remaining_budget_at_start':remaining_budget,'raw_entities_preserved':True,'warning_details_omitted':0}
    warning_bytes=0
    def warn_detail(message):
        nonlocal warning_bytes
        if optional_omissions:
            bounded=message[:MAX_WARNING_CHARS]
            cost=len(json.dumps(bounded,ensure_ascii=True).encode('ascii'))
            if len(warnings)>=MAX_WARNING_EXAMPLES or warning_bytes+cost>MAX_WARNING_BYTES:
                counts['warning_details_omitted']+=1;return
            warnings.append(bounded);warning_bytes+=cost
        else:warnings.append(message)
    for entity in entities:
        if not isinstance(entity,dict):raise ValueError('Invalid Source entity record')
        kind=entity.get('classname','')
        if not isinstance(kind,str):raise ValueError('Invalid Source light entity class')
        is_light=kind in SUPPORTED or kind.startswith('light_') or kind=='env_projectedtexture'
        if is_light:counts['light_entities']+=1
        if kind not in SUPPORTED:
            if is_light:
                warn_detail((kind[:160] if optional_omissions else kind)+': unsupported light entity retained in entities.json.')
                counts['unsupported_type']+=1
            continue
        try:row,warning,omission=_entity_light(entity,kind,scale)
        except ValueError as error:
            if not optional_omissions:raise
            counts['invalid']+=1
            name=str(entity.get('targetname',kind))[:160]
            warn_detail(name+': optional map light omitted ('+str(error)+'). Geometry and the raw entity are kept; review its light settings in entities.json.')
            continue
        if omission is not None:
            counts[omission]+=1;warn_detail(warning);continue
        if len(result)>=remaining_budget:
            if not optional_omissions:raise ValueError('Source map exceeds64supported static lights; split or simplify the map before import')
            counts['budget']+=1;continue
        result.append(row)
    counts['created']=len(result)
    if counts['budget']:
        warnings.append(str(counts['budget'])+' optional static map light(s) omitted by the global64-light limit. Geometry and all raw entities are kept; simplify map lighting or import a smaller scene to include them.')
    if counts['warning_details_omitted']:
        warnings.append(str(counts['warning_details_omitted'])+' additional per-light compatibility notes are summarized in the omission counts. All raw declarations are kept in entities.json; review their lighting settings there.')
    if result:
        if optional_omissions:
            warnings.append('Static Source entity lights use approximate intensity, attenuation and spotlight falloff; gameplay switching is not executed. Compatible static LDR brush lightmaps are reported separately; HDR, styled/displacement and ambient sky lighting are not reproduced.')
        else:
            warnings.append('Static Source entity lights use approximate intensity, attenuation and spotlight falloff; gameplay switching is not executed. Baked lightmaps, HDR/ambient sky lighting and animated styles are not recreated.')
    prepared={'lights':result,'warnings':warnings}
    if optional_omissions:prepared['omissions']=counts
    return prepared


def plan_batches(entity_batches,scale,*,optional_omissions=False):
    """One inventory/global budget across all SourceIO entity text blocks."""
    if not isinstance(entity_batches,list) or len(entity_batches)>256:raise ValueError('Invalid Source entity text inventory')
    entities=[]
    for batch in entity_batches:
        if not isinstance(batch,list) or len(entities)+len(batch)>100000:raise ValueError('Invalid Source entity inventory')
        entities.extend(batch)
    prepared=plan(entities,scale,optional_omissions=optional_omissions)
    prepared['entities']=entities
    return prepared

def create(bpy,prepared):
    from mathutils import Vector
    created=[]
    for row in prepared['lights']:
        light=bpy.data.lights.new('HAS '+row['name'],row['type']);light.color=row['color'];light.energy=row['energy']
        if row['type']=='SPOT':light.spot_size=row['spot_size'];light.spot_blend=row['spot_blend']
        obj=bpy.data.objects.new('HAS '+row['name'],light);bpy.context.scene.collection.objects.link(obj);obj.location=row['position']
        obj.rotation_euler=Vector(row['direction']).to_track_quat('-Z','Y').to_euler();created.append(obj)
    return created
