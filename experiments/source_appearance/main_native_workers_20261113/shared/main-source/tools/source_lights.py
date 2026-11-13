"""Bounded static Source entity lights; no entity programs, baked maps or photometry claim."""
import math
MAX_LIGHTS=64
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

def plan(entities,scale):
    if not isinstance(entities,list) or len(entities)>100000:raise ValueError('Invalid Source entity inventory')
    if not isinstance(scale,(int,float)) or isinstance(scale,bool) or not math.isfinite(scale) or not .0001<=scale<=10000:raise ValueError('Invalid Source light unit scale')
    result=[];warnings=[]
    for entity in entities:
        if not isinstance(entity,dict):raise ValueError('Invalid Source entity record')
        kind=entity.get('classname','')
        if not isinstance(kind,str):raise ValueError('Invalid Source light entity class')
        if kind not in SUPPORTED:
            if kind.startswith('light_') or kind=='env_projectedtexture':warnings.append(kind+': unsupported light entity retained in entities.json.')
            continue
        name=str(entity.get('targetname',kind))[:160]
        flags=scalar(entity,'spawnflags',0);style=scalar(entity,'style',0)
        if not flags.is_integer() or not 0<=flags<=4294967295 or not style.is_integer() or not 0<=style<=255:raise ValueError('Invalid Source light flags/style: '+name)
        if int(flags)&1:
            warnings.append(name+': starts-off light retained in entities.json; not enabled in the imported scene.');continue
        if style!=0:
            warnings.append(name+': animated light style is unsupported; retained in entities.json.');continue
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
            if not 0<outer<90 or not 0<=inner<=outer:raise ValueError('Invalid Source spotlight cone: '+name)
            row.update(spot_size=math.radians(outer*2),spot_blend=1-inner/outer)
        if len(result)>=MAX_LIGHTS:raise ValueError('Source map exceeds64supported static lights; split or simplify the map before import')
        result.append(row)
    if result:warnings.append('Static Source entity lights use approximate intensity, attenuation and spotlight falloff; gameplay switching is not executed. Baked lightmaps, HDR/ambient sky lighting and animated styles are not recreated.')
    return {'lights':result,'warnings':warnings}

def create(bpy,prepared):
    from mathutils import Vector
    created=[]
    for row in prepared['lights']:
        light=bpy.data.lights.new('HAS '+row['name'],row['type']);light.color=row['color'];light.energy=row['energy']
        if row['type']=='SPOT':light.spot_size=row['spot_size'];light.spot_blend=row['spot_blend']
        obj=bpy.data.objects.new('HAS '+row['name'],light);bpy.context.scene.collection.objects.link(obj);obj.location=row['position']
        obj.rotation_euler=Vector(row['direction']).to_track_quat('-Z','Y').to_euler();created.append(obj)
    return created
