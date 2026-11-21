"""Compile a deliberately bounded Source sprite subset into native time samples.

Own deterministic random stream/analytic motion: not Source engine bit equivalence.
Unknown operators, active operator fades, children and nonzero drag refuse whole
effects. Raw native data remains in the preparation report, never silently pruned.
"""
import math
from asset_audit import AssetError

FORMAT='studio_sprite_effect_1'
MAX_PARTICLES=1024
COMMON={'operator end fadein','operator end fadeout','operator fade oscillate','operator start fadein','operator start fadeout'}
BASE_FIELDS={'preventNameBasedLookup','max_particles','initial_particles','material','snapshot','cull_replacement_definition','fallback replacement definition','bounding_box_min','bounding_box_max','cull_radius','cull_cost','cull_control_point','radius','color','rotation','rotation_speed','sequence_number','sequence_number 1','group id','maximum time step','maximum sim tick rate','minimum sim tick rate','minimum rendered frames','control point to disable rendering if it is the camera','maximum draw distance','time to sleep when not drawn','Sort particles','batch particle systems','view model effect','screen space effect'}
FIELDS={
 'render_animated_sprites':{'animation rate','animation_fit_lifetime','orientation_type','second sequence animation rate','use animation rate as FPS','Visibility Proxy Input Control Point Number','Visibility Proxy Radius','Visibility input minimum','Visibility input maximum','Visibility Alpha Scale minimum','Visibility Alpha Scale maximum','Visibility Radius Scale minimum','Visibility Radius Scale maximum','Visibility Camera Depth Bias','orientation control point'},
 'emit_continuously':{'emission_duration','emission_rate','emission_start_time','scale emission to used control points','use parent particles for emission scaling'},
 'emit_instantaneously':{'emission_start_time','num_to_emit','maximum emission per frame','num_to_emit_minimum','emission count scale control point','emission count scale control point field'},
 'Lifetime Random':{'lifetime_min','lifetime_max','lifetime_random_exponent'},
 'Radius Random':{'radius_min','radius_max','radius_random_exponent'},
 'Alpha Random':{'alpha_min','alpha_max','alpha_random_exponent'},
 'Rotation Random':{'rotation_initial','rotation_offset_min','rotation_offset_max','rotation_random_exponent'},
 'Color Random':{'color1','color2','tint_perc','tint control point','tint clamp min','tint clamp max','tint update movement threshold'},
 'Position Within Sphere Random':{'bias in local system','control_point_number','create in model','distance_bias','distance_bias_absolute_value','distance_max','distance_min','randomly distribute to highest supplied Control Point','speed_in_local_coordinate_system_max','speed_in_local_coordinate_system_min','speed_max','speed_min','speed_random_exponent','randomly distribution growth time'},
 'Position Modify Offset Random':{'control_point_number','offset in local space 0/1','offset max','offset min','offset proportional to radius 0/1'},
 'Movement Basic':{'drag','gravity','max constraint passes'},
 'Lifespan Decay':set(),
 'Alpha Fade and Decay':{'end_alpha','end_fade_in_time','end_fade_out_time','start_alpha','start_fade_in_time','start_fade_out_time'},
 'Radius Scale':{'ease_in_and_out','end_time','radius_end_scale','radius_start_scale','scale_bias','start_time'},
 'Color Fade':{'color_fade','fade_start_time','fade_end_time','ease_in_and_out'},
}

def number(value,low=-100000,high=100000):
    if isinstance(value,bool)or not isinstance(value,(int,float))or not math.isfinite(value)or not low<=value<=high:raise AssetError('Invalid particle numeric value')
    return float(value)

def vector(value,count=3,low=-100000,high=100000):
    if not isinstance(value,list)or len(value)!=count:raise AssetError('Invalid particle vector')
    return[number(v,low,high)for v in value]

def xyz(value,scale):
    v=vector(value);return[v[0]*scale,v[2]*scale,-v[1]*scale]

def compile_effect(system,duration=10.,seed=17,scale=.01905):
    duration=number(duration,.01,60);scale=number(scale,.0001,1)
    if not isinstance(seed,int)or isinstance(seed,bool)or not 1<=seed<2147483647:raise AssetError('Invalid particle seed')
    if not isinstance(system,dict)or not isinstance(system.get('name'),str)or not 1<=len(system['name'])<=256:raise AssetError('Invalid particle system name')
    groups=system['groups'];base=system['parameters'];params={}
    if set(base)-BASE_FIELDS:raise AssetError('Unsupported particle system parameters: '+', '.join(sorted(set(base)-BASE_FIELDS)))
    if set(groups)-{'renderers','emitters','initializers','operators','children','constraints','forces'}:raise AssetError('Unsupported particle group')
    if base.get('control point to disable rendering if it is the camera',-1)!=-1:raise AssetError('Camera control-point visibility unsupported')
    for group in ['children','constraints','forces']:
        if groups.get(group):raise AssetError('Unsupported particle '+group+'; effect not partially imported')
    expected={'renderers':{'render_animated_sprites'},'emitters':{'emit_continuously','emit_instantaneously'},'initializers':{'Lifetime Random','Radius Random','Alpha Random','Rotation Random','Color Random','Position Within Sphere Random','Position Modify Offset Random'},'operators':{'Movement Basic','Lifespan Decay','Alpha Fade and Decay','Radius Scale','Color Fade'}}
    for group,allowed in expected.items():
        for item in groups.get(group,[]):
            name=item['function'];p=item['parameters']
            if name not in allowed:raise AssetError('Unsupported particle operator: '+name)
            if name in params:raise AssetError('Repeated particle operator not supported: '+name)
            if set(p)-FIELDS[name]-COMMON:raise AssetError('Unsupported parameters for '+name+': '+', '.join(sorted(set(p)-FIELDS[name]-COMMON)))
            if any(number(p.get(key,0))!=0 for key in COMMON):raise AssetError('Active operator timing/fades unsupported: '+name)
            params[name]=p
    if len(groups.get('renderers',[]))!=1 or len(groups.get('emitters',[]))!=1:raise AssetError('Select one sprite renderer/emitter')
    for key in ['snapshot','cull_replacement_definition','fallback replacement definition']:
        if base.get(key,''):raise AssetError('Unsupported particle snapshot/replacement')
    for key in ['view model effect','screen space effect']:
        if base.get(key,False):raise AssetError('View-model/screen-space particles unsupported')
    if base.get('initial_particles',0)!=0 or base.get('sequence_number',0)!=0 or base.get('sequence_number 1',0)!=0:raise AssetError('Initial particles/nonzero texture sequences unsupported')
    cap=int(number(base.get('max_particles',1000),1,MAX_PARTICLES))
    if cap!=base.get('max_particles',1000):raise AssetError('Noninteger maximum particle count')
    renderer=params['render_animated_sprites']
    if renderer.get('orientation_type',0)!=0 or renderer.get('orientation control point',-1)!=-1 or renderer.get('Visibility Proxy Input Control Point Number',-1)!=-1 or renderer.get('second sequence animation rate',0)!=0:raise AssetError('Only camera-facing fixed-texture sprites supported')
    # Animation rate is inert only after material decoding proves a single image,
    # without a sprite-sheet resource. It is retained in the native report.
    p=params.get('emit_continuously',params.get('emit_instantaneously',{}));start=number(p.get('emission_start_time',0),0,60)
    if 'emit_continuously'in params:
        if p.get('scale emission to used control points',0)!=0 or p.get('use parent particles for emission scaling',False):raise AssetError('Parent/control-point emission unsupported')
        rate=number(p.get('emission_rate',100),.001,10000);length=number(p.get('emission_duration',0),0,60);end=min(duration,start+length)if length else duration
        count=max(0,math.ceil((end-start)*rate));births=[start+i/rate for i in range(count)] if count<=MAX_PARTICLES else []
    else:
        if p.get('num_to_emit_minimum',-1)!=-1 or p.get('emission count scale control point',-1)!=-1:raise AssetError('Random/scaled emission count unsupported')
        count=int(number(p.get('num_to_emit',1),0,MAX_PARTICLES));births=[start]*count
        if count!=p.get('num_to_emit',1):raise AssetError('Noninteger emission count')
        if count>number(p.get('maximum emission per frame',100),1,MAX_PARTICLES):raise AssetError('Multi-frame instantaneous emission unsupported')
    if count>MAX_PARTICLES:raise AssetError('Particle preparation exceeds1024 births; shorten duration')
    gravity=params.get('Movement Basic',{});drag=number(gravity.get('drag',0),0,10000)
    if drag:raise AssetError('Nonzero native drag is not yet supported')
    sphere=params.get('Position Within Sphere Random',{})
    if sphere.get('bias in local system',False):raise AssetError('Local-space spherical bias unsupported')
    for key,default in [('control_point_number',0),('create in model',0),('randomly distribute to highest supplied Control Point',False),('randomly distribution growth time',0)]:
        if sphere.get(key,default)!=default:raise AssetError('Unsupported spherical model/control-point behavior')
    if sphere.get('distance_bias',[0,0,0])not in[[0,0,0],[1,1,1]]or sphere.get('distance_bias_absolute_value',[0,0,0])!=[0,0,0]:raise AssetError('Biased spherical distribution unsupported')
    for key in ['speed_in_local_coordinate_system_min','speed_in_local_coordinate_system_max']:
        if sphere.get(key,[0,0,0])!=[0,0,0]:raise AssetError('Directional local velocity unsupported')
    offset=params.get('Position Modify Offset Random',{})
    if offset.get('control_point_number',0)!=0 or offset.get('offset proportional to radius 0/1',False) or offset.get('offset in local space 0/1',False):raise AssetError('Unsupported offset control-point behavior')
    color=params.get('Color Random',{})
    if color.get('tint_perc',0)!=0:raise AssetError('Control-point tint unsupported')
    alpha=params.get('Alpha Fade and Decay',{});fade={'in_start':number(alpha.get('start_fade_in_time',0),0,1),'in_end':number(alpha.get('end_fade_in_time',.1),0,1),'out_start':number(alpha.get('start_fade_out_time',.9),0,1),'out_end':number(alpha.get('end_fade_out_time',1),0,1),'start_alpha':number(alpha.get('start_alpha',0),0,1),'end_alpha':number(alpha.get('end_alpha',0),0,1)}
    if not alpha:fade.update(in_start=0,in_end=0,out_start=1,out_end=1,start_alpha=1,end_alpha=1)
    if not 0<=fade['in_start']<=fade['in_end']<=fade['out_start']<=fade['out_end']<=1:raise AssetError('Overlapping/reversed particle alpha ramps')
    radius=params.get('Radius Scale',{});radius_curve={'start':number(radius.get('start_time',0),0,1),'end':number(radius.get('end_time',1),0,1),'from':number(radius.get('radius_start_scale',1),0,100),'to':number(radius.get('radius_end_scale',1),0,100),'bias':number(radius.get('scale_bias',.5),.001,.999),'ease':radius.get('ease_in_and_out',False)}
    if radius_curve['start']>radius_curve['end']or not isinstance(radius_curve['ease'],bool):raise AssetError('Invalid particle radius ramp')
    cf=params.get('Color Fade',{});color_curve={'enabled':bool(cf),'start':number(cf.get('fade_start_time',0),0,1),'end':number(cf.get('fade_end_time',1),0,1),'to':[v/255 for v in vector(cf.get('color_fade',[255,255,255,255]),4,0,255)],'ease':cf.get('ease_in_and_out',False)}
    if color_curve['start']>color_curve['end']or not isinstance(color_curve['ease'],bool):raise AssetError('Invalid particle color ramp')
    state=seed
    def random():
        nonlocal state
        state=state*48271%2147483647;return state/2147483647
    def pick(lo,hi,exponent=1):return number(lo)+(number(hi)-number(lo))*random()**number(exponent,.01,100)
    def rand_pair(name,prefix,default):
        p=params.get(name,{});return pick(p.get(prefix+'_min',default),p.get(prefix+'_max',default),p.get(prefix+'_random_exponent',1))
    particles=[];base_color=vector(base.get('color',[255]*4),4,0,255)
    for birth in births:
        lifetime=rand_pair('Lifetime Random','lifetime',1)
        if not .001<=lifetime<=60:raise AssetError('Particle lifetime outside supported range')
        z=pick(-1,1);angle=pick(0,2*math.pi);radial=[math.sqrt(max(0,1-z*z))*math.cos(angle),math.sqrt(max(0,1-z*z))*math.sin(angle),z]
        distance=pick(sphere.get('distance_min',0),sphere.get('distance_max',0));speed=pick(sphere.get('speed_min',0),sphere.get('speed_max',0),sphere.get('speed_random_exponent',1))
        off=[pick(a,b)for a,b in zip(vector(offset.get('offset min',[0,0,0])),vector(offset.get('offset max',[0,0,0])))]
        position=xyz([radial[i]*distance+off[i]for i in range(3)],scale);velocity=xyz([v*speed for v in radial],scale)
        c1=vector(color.get('color1',base_color),4,0,255);c2=vector(color.get('color2',base_color),4,0,255);rgb=[pick(c1[i],c2[i])/255 for i in range(3)]
        a=rand_pair('Alpha Random','alpha',base_color[3])/255;rad=rand_pair('Radius Random','radius',base.get('radius',5))*scale
        if not 0<=a<=1 or not 0<rad<=1000:raise AssetError('Particle alpha/radius outside supported range')
        rp=params.get('Rotation Random',{});rot=number(rp.get('rotation_initial',base.get('rotation',0)))+pick(rp.get('rotation_offset_min',0),rp.get('rotation_offset_max',360),rp.get('rotation_random_exponent',1))
        particles.append({'birth':birth,'lifetime':lifetime,'position':position,'velocity':velocity,'acceleration':xyz(gravity.get('gravity',[0,0,0]),scale),'radius':rad,'color':rgb+[a],'rotation':math.radians(rot),'spin':math.radians(number(base.get('rotation_speed',0)))})
    for row in particles:
        if sum(p['birth']<=row['birth']<p['birth']+p['lifetime']for p in particles)>cap:raise AssetError('Native particle cap would drop emissions; not partially approximated')
    return {'format':FORMAT,'name':system['name'],'duration':duration,'max_particles':cap,'seed':seed,'particles':particles,'alpha':fade,'radius':radius_curve,'color':color_curve,'source_scale':scale,'interpretation':'HAS deterministic sprite approximation; own random stream, no Source bit equivalence'}
