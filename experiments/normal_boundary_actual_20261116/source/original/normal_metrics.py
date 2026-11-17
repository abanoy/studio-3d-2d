"""Stdlib scalar normal diagnostics; raw gate and direction metrics stay separate."""
import math

EPS=2e-5


def vector(value):
    if len(value)!=3 or any(type(v) not in (int,float) or not math.isfinite(v) for v in value):raise ValueError('Finite normal vector required')
    return tuple(float(v) for v in value)


def length(value):return math.sqrt(sum(v*v for v in vector(value)))
def distance(a,b):return length(tuple(x-y for x,y in zip(vector(a),vector(b))))


def unit(value):
    value=vector(value);size=length(value)
    return None if size==0 else tuple(v/size for v in value)


def pair(a,b):
    a,b=vector(a),vector(b);ua,ub=unit(a),unit(b)
    return {'raw_distance':distance(a,b),'unit_direction_distance':None if ua is None or ub is None else distance(ua,ub),'left_length_deviation':abs(length(a)-1),'right_length_deviation':abs(length(b)-1)}


def stats(values):
    finite=sorted(v for v in values if v is not None)
    return {'count':len(finite),'undefined':len(values)-len(finite),'min':finite[0] if finite else None,'max':finite[-1] if finite else None,'mean':sum(finite)/len(finite) if finite else None,'p50':finite[len(finite)//2] if finite else None,'p99':finite[min(len(finite)-1,int(len(finite)*.99))] if finite else None,'diagnostic_above_2e_5':sum(v>EPS for v in finite)}


def summarize(rows):
    return {key:stats([row[key] for row in rows]) for key in ('raw_distance','unit_direction_distance','left_length_deviation','right_length_deviation')}


def candidate_bounds(native,targets):
    rows=[pair(native,target) for target in targets]
    if not rows:raise ValueError('At least one compatible witness required')
    raw=[row['raw_distance'] for row in rows]
    directions=[row['unit_direction_distance'] for row in rows if row['unit_direction_distance'] is not None]
    return {'raw_best':min(raw),'raw_worst':max(raw),'unit_best':min(directions) if directions else None,'unit_worst':max(directions) if directions else None}


def exporter_axis_stage(value):
    """Independent scalar expectation AFTER normalization/skin transform."""
    value=vector(value)
    if value==(0.,0.,0.):value=(0.,0.,1.)
    return value[0],value[2],-value[1]
