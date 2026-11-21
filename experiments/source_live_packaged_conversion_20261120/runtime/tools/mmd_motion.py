"""Bounded VMD2 data reader and source-time sampler; no native code execution."""
from bisect import bisect_right
import hashlib
import math
from pathlib import Path
import struct

MAX_BYTES=32*1024*1024
MAX_KEYS=200000
MAX_TRACKS=4096


class Reader:
    def __init__(self,data):
        self.data=data
        self.at=0
        self.total=0

    def take(self,size):
        if size<0 or self.at+size>len(self.data):raise ValueError("Truncated VMD section")
        value=self.data[self.at:self.at+size]
        self.at+=size
        return value

    def unpack(self,layout):return struct.unpack(layout,self.take(struct.calcsize(layout)))

    def count(self,width):
        count,=self.unpack("<I")
        self.total+=count
        if self.total>MAX_KEYS or count*width>len(self.data)-self.at:
            raise ValueError("Invalid or excessive VMD section count")
        return count

    def frame(self):
        value,=self.unpack("<I")
        if value>1000000:raise ValueError("VMD frame exceeds the supported source range")
        return value

    def numbers(self,width):
        values=self.unpack("<"+"f"*width)
        if not all(math.isfinite(v) and abs(v)<=1e9 for v in values):raise ValueError("Invalid VMD numeric value")
        return list(values)

    def flag(self):
        value=self.take(1)[0]
        if value not in (0,1):raise ValueError("Invalid VMD switch")
        return bool(value)


def name(raw):
    raw=raw.split(b"\0",1)[0]
    try:return raw.decode("cp932")
    except UnicodeError as error:raise ValueError("VMD name cannot be decoded exactly") from error


def curves(raw):
    # MMD's four redundant 16-byte blocks: use each block's own coordinates.
    # Some exporters leave the first block's redundant Z/rotation bytes zero.
    result=[tuple(raw[base+i] for i in (0,4,8,12)) for base in (0,16,32,48)]
    if any(v>127 for row in result for v in row):raise ValueError("Invalid VMD Bezier control")
    return result


def read_motion(path):
    with Path(path).open("rb") as stream:data=stream.read(MAX_BYTES+1)
    if len(data)>MAX_BYTES:raise ValueError("VMD exceeds 32 MiB")
    reader=Reader(data)
    if reader.take(30).rstrip(b"\0")!=b"Vocaloid Motion Data 0002":raise ValueError("Expected a VMD version 2 motion")
    model=name(reader.take(20))
    bones={};morphs={};counts={};seen=set();properties=[]
    for _ in range(reader.count(111)):
        native=name(reader.take(15));frame=reader.frame()
        if not native or (native,frame) in seen:raise ValueError("Empty or duplicate VMD bone key")
        seen.add((native,frame))
        position=reader.numbers(3);rotation=reader.numbers(4)
        if not any(rotation):rotation=[0.,0.,0.,1.]
        interpolation=curves(reader.take(64))
        bones.setdefault(native,[]).append(dict(frame=frame,position=position,rotation_xyzw=rotation,curves=interpolation))
        if len(bones)>MAX_TRACKS:raise ValueError("VMD has too many bone tracks")
    # Older writers may omit later sections, but never accept half a count/key.
    if reader.at<len(data):
        seen=set()
        for _ in range(reader.count(23)):
            native=name(reader.take(15));frame=reader.frame();weight=reader.numbers(1)[0]
            if not native or (native,frame) in seen:raise ValueError("Empty or duplicate VMD shape key")
            if abs(weight)>100:raise ValueError("VMD shape exceeds the standard amount range")
            seen.add((native,frame));morphs.setdefault(native,[]).append(dict(frame=frame,weight=weight))
            if len(morphs)>MAX_TRACKS:raise ValueError("VMD has too many shape tracks")
    for section,width in (("camera",61),("light",28),("self_shadow",9),("properties",9)):
        if reader.at==len(data):break
        count=reader.count(width);counts[section]=count
        for _ in range(count):
            frame=reader.frame()
            if section=="camera":
                reader.numbers(7);interpolation=reader.take(24)
                if any(v>127 for v in interpolation):raise ValueError("Invalid camera Bezier control")
                reader.unpack("<I");reader.flag()
            elif section=="light":reader.numbers(6)
            elif section=="self_shadow":
                if reader.take(1)[0]>2:raise ValueError("Invalid VMD shadow mode")
                reader.numbers(1)
            else:
                visible=reader.flag();ik_count=reader.count(21);states={}
                counts["ik_switches"]=counts.get("ik_switches",0)+ik_count
                if ik_count>MAX_TRACKS:raise ValueError("VMD property has too many IK switches")
                for _ in range(ik_count):
                    native=name(reader.take(20)[:15]);state=reader.flag()
                    if not native or native in states:raise ValueError("Invalid or repeated VMD IK switch")
                    states[native]=state
                properties.append(dict(frame=frame,visible=visible,ik_states=states))
    if reader.at!=len(data):raise ValueError("Unexpected trailing VMD data")
    for tracks in (bones,morphs):
        for keys in tracks.values():keys.sort(key=lambda key:key["frame"])
    last=max((key["frame"] for tracks in (bones,morphs) for keys in tracks.values() for key in keys),default=0)
    properties.sort(key=lambda key:key["frame"])
    if len({key["frame"] for key in properties})!=len(properties):raise ValueError("Repeated VMD property frame")
    last=max(last,max((key["frame"] for key in properties if key["ik_states"]),default=0))
    return dict(format="studio_mmd_motion_input_1",source_sha256=hashlib.sha256(data).hexdigest(),source_model=model,
                source_fps=30,bones=bones,morphs=morphs,last_frame=last,properties=properties,other_sections=counts)


def bezier(x,points):
    if not 0<=x<=1:raise ValueError("Bezier input must lie inside the interval")
    x1,y1,x2,y2=(v/127. for v in points)
    if x1==y1 and x2==y2:return x
    lo,hi=0.,1.
    for _ in range(48):
        t=(lo+hi)/2;u=1-t
        at=3*u*u*t*x1+3*u*t*t*x2+t*t*t
        if at<x:lo=t
        else:hi=t
    t=(lo+hi)/2;u=1-t
    return 3*u*u*t*y1+3*u*t*t*y2+t*t*t


def normalize(q):
    length=math.sqrt(sum(v*v for v in q))
    return tuple(v/length for v in q) if length else (0.,0.,0.,1.)


def slerp(a,b,t):
    a=normalize(a);b=normalize(b);dot=sum(x*y for x,y in zip(a,b))
    if dot<0:b=tuple(-v for v in b);dot=-dot
    dot=min(1.,max(-1.,dot))
    if dot>.9995:return normalize(tuple(x+(y-x)*t for x,y in zip(a,b)))
    angle=math.acos(dot);den=math.sin(angle)
    return tuple((math.sin((1-t)*angle)*x+math.sin(t*angle)*y)/den for x,y in zip(a,b))


class Sampler:
    def __init__(self,motion):
        self.motion=motion
        self.times={kind:{native:[key["frame"] for key in keys] for native,keys in motion[kind].items()} for kind in ("bones","morphs")}
        self.ik={}
        for key in motion.get("properties",[]):
            for native,value in key["ik_states"].items():self.ik.setdefault(native,[]).append((key["frame"],value))
        self.ik_times={native:[key[0] for key in keys] for native,keys in self.ik.items()}

    def pair(self,kind,native,frame):
        keys=self.motion[kind][native];times=self.times[kind][native]
        if frame<=times[0]:return keys[0],keys[0],0.
        if frame>=times[-1]:return keys[-1],keys[-1],0.
        at=bisect_right(times,frame)-1;a,b=keys[at:at+2]
        return a,b,(frame-a["frame"])/(b["frame"]-a["frame"])

    def sample(self,frame):
        if not isinstance(frame,(int,float)) or not math.isfinite(frame) or not 0<=frame<=1000000:raise ValueError("Invalid VMD sample frame")
        bones=[];morphs=[]
        for native in self.motion["bones"]:
            a,b,t=self.pair("bones",native,frame)
            factors=[bezier(t,curve) for curve in b["curves"]]
            position=[x+(y-x)*factor for x,y,factor in zip(a["position"],b["position"],factors)]
            bones.append(dict(name=native,position=position,rotation_xyzw=slerp(a["rotation_xyzw"],b["rotation_xyzw"],factors[3])))
        for native in self.motion["morphs"]:
            a,b,t=self.pair("morphs",native,frame)
            morphs.append(dict(name=native,weight=a["weight"]+(b["weight"]-a["weight"])*t))
        states={}
        for native,keys in self.ik.items():
            index=bisect_right(self.ik_times[native],frame)-1
            if index>=0:states[native]=keys[index][1]
        return dict(format="studio_mmd_pose_input_1",source_sha256=self.motion["source_sha256"],source_model=self.motion["source_model"],bones=bones,morphs=morphs,ik_enabled=states)

    def sample_project_frame(self,offset,fps_num,fps_den=1,source_start=0):
        if type(offset) is not int or offset<0 or type(fps_num) is not int or not 1<=fps_num<=240000 or type(fps_den) is not int or not 1<=fps_den<=10000:
            raise ValueError("Invalid destination frame rate or offset")
        return self.sample(source_start+offset*30*fps_den/fps_num)
