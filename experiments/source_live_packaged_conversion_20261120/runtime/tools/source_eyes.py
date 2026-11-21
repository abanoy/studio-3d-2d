"""Bounded neutral iris projection into ordinary GLB UVs; no native shader execution."""
import math


def project(points, radius, offset):
    radius=float(radius);offset=float(offset)
    if not math.isfinite(radius) or not 1e-6<=radius<=10000 or not math.isfinite(offset) or abs(offset)>math.pi:
        raise ValueError('Invalid native eye radius or offset')
    result=[];cosine=math.cos(offset);sine=math.sin(offset)
    for point in points:
        if len(point)!=3 or not all(math.isfinite(v)and abs(v)<=1e6 for v in point):
            raise ValueError('Invalid native eye coordinates')
        x,y,z=point
        uv=(.5+(cosine*x+sine*y)/(2*radius),.5+z/(2*radius))
        if not all(math.isfinite(v)and abs(v)<=1e6 for v in uv):raise ValueError('Native eye projection exceeds bounds')
        result.append(uv)
        if len(result)>1000000:raise ValueError('Native eye projection exceeds loop budget')
    return result


def plan(material, objects):
    """Validate an unambiguous native helper and stage all UV edits before applying.

    Blender objects are passed in; importing this module needs no Blender/NumPy.
    Reciprocal native iris_scale is the helper's radius, not its diameter.
    Projection is a static neutral approximation, not Source's ray-traced eye.
    """
    eye=material.get('eye_source')
    if eye is None or getattr(eye,'type',None)!='EMPTY':raise ValueError('Native eye helper unavailable')
    owners=[o for o in objects if o.type=='MESH'and any(s.material==material for s in o.material_slots)]
    if len(owners)!=1:raise ValueError('Native eye material needs one unambiguous mesh/helper binding')
    obj=owners[0];radius_key=eye.name+'_iris_scale';offset_key=eye.name+'_z_offset'
    if radius_key not in obj or offset_key not in obj or obj.data.uv_layers.active is None:
        raise ValueError('Native eye helper parameters or UVs unavailable')
    if not all(math.isfinite(v)for row in eye.matrix_world for v in row):raise ValueError('Invalid native eye frame')
    matrix=eye.matrix_world.inverted()@obj.matrix_world
    loops=[i for face in obj.data.polygons if obj.material_slots[face.material_index].material==material for i in face.loop_indices]
    if not loops:raise ValueError('Native eye material has no faces')
    radius=float(obj[radius_key]);offset=float(obj[offset_key])
    points=[tuple(matrix@obj.data.vertices[obj.data.loops[i].vertex_index].co)for i in loops]
    values=project(points,radius,offset)
    return {'object':obj,'changes':list(zip(loops,values)),
            'report':{'format':'studio_neutral_eye_1','mesh':obj.name,'helper':eye.name,
                      'iris_radius':radius,'offset_radians':offset,'loops':len(loops),
                      'note':'Baked neutral iris; gaze, refraction, dilation and native eye shading are not reproduced'}}
