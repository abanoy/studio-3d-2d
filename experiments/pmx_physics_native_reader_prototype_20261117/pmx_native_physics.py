"""Bounded PMX2.0 prefix walk and lossless native physics-table capsule.

In-memory immutable bytes only. No file I/O, dependencies, source conversion,
model validity claim, native execution, scaling or integration. Geometry is
walked only to find tables. Physics binary32 values are retained as raw words,
including nonfinite words; their numerical/physical validity is unassessed.
"""
from dataclasses import dataclass, fields
import hashlib
import json

class Refusal(ValueError):
    pass

@dataclass(frozen=True)
class Limits:
    source_bytes:int=128*1024*1024
    string_bytes:int=1024*1024
    total_string_bytes:int=8*1024*1024
    retained_name_utf8_bytes:int=1024
    vertices:int=2_000_000
    face_indices:int=12_000_000
    textures:int=10_000
    materials:int=10_000
    bones:int=4096
    morphs:int=4096
    morph_offsets:int=1_000_000
    displays:int=4096
    display_elements:int=65_536
    ik_links:int=65_536
    rigid_bodies:int=512
    joints:int=1024
    operations:int=20_000_000
    metadata_bytes:int=2*1024*1024

_HARD=Limits()
RIGID_F32_LAYOUT=(('size',0,3),('location',3,3),('rotation',6,3),('mass',9,1),('velocity_attenuation',10,1),('rotation_attenuation',11,1),('bounce',12,1),('friction',13,1))
JOINT_F32_LAYOUT=(('location',0,3),('rotation',3,3),('minimum_location',6,3),('maximum_location',9,3),('minimum_rotation',12,3),('maximum_rotation',15,3),('linear_spring',18,3),('angular_spring',21,3))

def _limits(value):
    if type(value) is not Limits:raise Refusal('limits type')
    for f in fields(Limits):
        n=getattr(value,f.name)
        if type(n) is not int or n<0 or n>getattr(_HARD,f.name):raise Refusal('invalid or widened budget: '+f.name)

class _Cursor:
    def __init__(self,data,limits):
        self.data=data;self.limit=limits;self.pos=0;self.ops=0;self.string_bytes=0
        self.counts={};self.widths={};self.encoding='';self.deferred={};self.aggregate={};self.metadata_reserved=0
        self.reserve(4096)
    def reserve(self,n):
        self.metadata_reserved+=n
        if self.metadata_reserved>self.limit.metadata_bytes:raise Refusal('conservative retained metadata budget')
    def tick(self,n=1):
        self.ops+=n
        if self.ops>self.limit.operations:raise Refusal('operation budget')
    def region(self,n,label):
        self.tick()
        if type(n) is not int or n<0 or n>len(self.data)-self.pos:raise Refusal('truncated '+label+' at '+str(self.pos))
        start=self.pos;self.pos+=n;return start
    def take(self,n,label):
        start=self.region(n,label);return self.data[start:self.pos]
    def skip(self,n,label):self.region(n,label)
    def integer(self,n,signed,label):return int.from_bytes(self.take(n,label),'little',signed=signed)
    def i32(self,label):return self.integer(4,True,label)
    def u8(self,label):return self.integer(1,False,label)
    def count(self,kind,minimum=0):
        start=self.pos;n=self.i32(kind+' count')
        cap=getattr(self.limit,kind)
        if n<0 or n>cap:raise Refusal('count budget '+kind)
        if minimum and n>(len(self.data)-self.pos)//minimum:raise Refusal('truncated table '+kind)
        self.counts[kind]=n;return n,start
    def total(self,kind,n):
        value=self.aggregate.get(kind,0)+n
        if n<0 or value>getattr(self.limit,kind):raise Refusal('aggregate budget '+kind)
        self.aggregate[kind]=value
    def text(self,label,retain=False):
        start=self.pos;n=self.i32(label+' byte length')
        if n<0 or n>self.limit.string_bytes:raise Refusal('string budget '+label)
        self.string_bytes+=n
        if self.string_bytes>self.limit.total_string_bytes:raise Refusal('aggregate string budget')
        word=self.take(n,label)
        try:decoded=word.decode(self.encoding,errors='strict')
        except UnicodeError as exc:raise Refusal('invalid '+self.encoding+' '+label) from exc
        if retain:
            if len(decoded.encode('utf-8'))>self.limit.retained_name_utf8_bytes:raise Refusal('retained name budget '+label)
            self.reserve(2*n+6*len(decoded.encode('utf-8'))+256)
            return {'text':decoded,'raw_hex':word.hex(),'offset':start,'payload_offset':start+4,'bytes':n,'encoding':self.encoding}
        return None
    def floats(self,n,label):
        self.reserve(n*32+256)
        start=self.pos;word=self.take(n*4,label)
        words=[word[i:i+4].hex() for i in range(0,len(word),4)]
        # Classify, without converting or normalizing any F32 word.
        nonfinite=[i for i in range(n) if int.from_bytes(word[4*i:4*i+4],'little')&0x7f800000==0x7f800000]
        return {'offset':start,'words_le_hex':words,'nonfinite_word_indices':nonfinite}
    def index(self,kind,label,absent=True,retain=False):
        width=self.widths[kind];signed=kind!='vertices';start=self.pos
        word=self.take(width,label);value=int.from_bytes(word,'little',signed=signed)
        if signed and value<(-1 if absent else 0):raise Refusal('invalid negative reference '+label)
        if not signed and value<0:raise Refusal('invalid unsigned reference '+label)
        if value>=0:
            if kind in self.counts:
                if value>=self.counts[kind]:raise Refusal('out-of-range reference '+label)
            else:self.deferred[kind]=max(value,self.deferred.get(kind,-1))
        if retain:
            self.reserve(256)
            return {'value':value,'word_le_hex':word.hex(),'offset':start,'width':width,'signed':signed}
        return value
    def close_deferred(self,kind):
        if self.deferred.get(kind,-1)>=self.counts[kind]:raise Refusal('out-of-range deferred '+kind+' reference')
    def enum(self,allowed,label):
        start=self.pos;value=self.u8(label)
        if value not in allowed:raise Refusal('unsupported '+label+' '+str(value))
        return value,start

def read_pmx20_physics(data,limits=Limits()):
    _limits(limits)
    if type(data) is not bytes:raise Refusal('input must be immutable bytes')
    if len(data)>limits.source_bytes:raise Refusal('source byte budget')
    c=_Cursor(data,limits)
    if c.take(4,'signature')!=b'PMX ':raise Refusal('unsupported PMX signature')
    version=c.take(4,'version')
    if version!=bytes.fromhex('00000040'):raise Refusal('unsupported PMX version; PMX2.1/soft bodies require separate support')
    if c.u8('global length')!=8:raise Refusal('unsupported globals length')
    encoding,_=c.enum((0,1),'encoding');c.encoding='utf-16-le' if encoding==0 else 'utf-8'
    uv,_=c.enum(range(5),'additional UV count')
    for kind in ('vertices','textures','materials','bones','morphs','rigid_bodies'):
        width,_=c.enum((1,2,4),kind+' index width');c.widths[kind]=width
    model_names=[c.text(label,True) for label in ('model name','model English name')]
    # Comments are strictly decoded and bounded, not placed in the metadata capsule.
    for label in ('model comment','model English comment'):c.text(label)
    sections={}
    def begin(kind,minimum=0):
        n,start=c.count(kind,minimum);sections[kind]={'count':n,'count_offset':start,'count_word_le_hex':data[start:start+4].hex(),'data_offset':c.pos};return n
    def end(kind):sections[kind]['end_offset']=c.pos
    vertices=begin('vertices',37+uv*16+c.widths['bones'])
    for _ in range(vertices):
        c.skip(32+uv*16,'vertex vectors');deform,_=c.enum((0,1,2,3),'vertex deform')
        for _ in range((1,2,4,2)[deform]):c.index('bones','vertex weight bone')
        c.skip((0,4,16,40)[deform]+4,'vertex weights/edge')
    end('vertices')
    indices=begin('face_indices',c.widths['vertices'])
    if indices%3:raise Refusal('face index count is not divisible by three')
    for _ in range(indices):c.index('vertices','face vertex',False)
    end('face_indices')
    for _ in range(begin('textures',4)):c.text('texture path')
    end('textures');c.close_deferred('textures')
    material_surfaces=0
    for _ in range(begin('materials',84+2*c.widths['textures'])):
        c.text('material name');c.text('material English name');c.skip(44,'material colors');c.enum(range(32),'material flags');c.skip(20,'material edge')
        c.index('textures','material texture');c.index('textures','material sphere texture')
        c.enum((0,1,2,3),'sphere mode');shared,_=c.enum((0,1),'shared toon flag')
        if shared:c.enum(range(10),'shared toon texture')
        else:c.index('textures','material toon texture')
        c.text('material comment');surfaces=c.i32('material face index count')
        if surfaces<0 or surfaces%3 or surfaces>indices:raise Refusal('invalid material face index count')
        material_surfaces+=surfaces
    end('materials')
    # This prefix policy checks index extents, not material coverage or geometry validity.
    bones=[]
    for i in range(begin('bones',26+2*c.widths['bones'])):
        c.reserve(512)
        start=c.pos;name=c.text('bone name',True);name_e=c.text('bone English name',True)
        bone={'native_index':i,'offset':start,'name':name,'name_e':name_e,'location':c.floats(3,'bone location'),'parent':c.index('bones','bone parent',True,True)}
        layer_start=c.pos;layer=c.i32('bone transform layer');flags_start=c.pos;flags=c.integer(2,False,'bone flags')
        if flags&~0x3f3f:raise Refusal('unsupported bone flags')
        bone.update(transform_layer={'offset':layer_start,'value':layer,'word_le_hex':data[layer_start:layer_start+4].hex()},flags={'offset':flags_start,'value':flags,'word_le_hex':data[flags_start:flags_start+2].hex()})
        if flags&1:bone['tail_bone']=c.index('bones','bone tail',True,True)
        else:bone['tail_offset']=c.floats(3,'bone tail offset')
        if flags&0x300:bone['grant']={'source':c.index('bones','grant bone',True,True),'influence':c.floats(1,'grant influence')}
        if flags&0x400:bone['fixed_axis']=c.floats(3,'bone fixed axis')
        if flags&0x800:bone['local_axes']=c.floats(6,'bone local axes')
        if flags&0x2000:
            offset=c.pos;value=c.i32('external parent key');bone['external_parent_key']={'offset':offset,'value':value,'word_le_hex':data[offset:offset+4].hex()}
        if flags&0x20:
            ik={'target':c.index('bones','IK target',True,True)};offset=c.pos;iterations=c.i32('IK iterations')
            if iterations<0:raise Refusal('negative IK iterations')
            ik['iterations']={'offset':offset,'value':iterations,'word_le_hex':data[offset:offset+4].hex()};ik['limit']=c.floats(1,'IK per-step limit')
            links=c.i32('IK link count');c.total('ik_links',links);ik['links']=[]
            if links>(len(data)-c.pos)//(c.widths['bones']+1):raise Refusal('truncated IK links')
            for _ in range(links):
                c.reserve(256)
                link={'bone':c.index('bones','IK link bone',True,True)};limited,offset=c.enum((0,1),'IK link limit flag');link['limited']={'offset':offset,'value':limited}
                if limited:link['angle_bounds']=c.floats(6,'IK angle bounds')
                ik['links'].append(link)
            bone['ik']=ik
        bone['end_offset']=c.pos;bones.append(bone)
    end('bones');c.close_deferred('bones')
    morphs=begin('morphs',14)
    for _ in range(morphs):
        c.text('morph name');c.text('morph English name');c.enum(range(5),'morph category');kind,_=c.enum(range(9),'morph type')
        offsets=c.i32('morph offset count');c.total('morph_offsets',offsets)
        record_size=(c.widths['morphs']+4,c.widths['vertices']+12,c.widths['bones']+28,*([c.widths['vertices']+16]*5),c.widths['materials']+113)[kind]
        if offsets>(len(data)-c.pos)//record_size:raise Refusal('truncated morph offsets')
        for _ in range(offsets):
            if kind==0:c.index('morphs','group morph',False);c.skip(4,'group morph weight')
            elif kind==1:c.index('vertices','vertex morph',False);c.skip(12,'vertex morph offset')
            elif kind==2:c.index('bones','bone morph',False);c.skip(28,'bone morph offset')
            elif kind<=7:c.index('vertices','UV morph',False);c.skip(16,'UV morph offset')
            else:c.index('materials','material morph',True);c.enum((0,1),'material morph operation');c.skip(112,'material morph values')
    end('morphs');c.close_deferred('morphs')
    for _ in range(begin('displays',13)):
        c.text('display name');c.text('display English name');c.enum((0,1),'special display flag')
        elements=c.i32('display element count');c.total('display_elements',elements)
        if elements>(len(data)-c.pos)//2:raise Refusal('truncated display elements')
        for _ in range(elements):
            kind,_=c.enum((0,1),'display element tag');c.index('bones' if kind==0 else 'morphs','display element',False)
    end('displays')
    bodies=[]
    for i in range(begin('rigid_bodies',69+c.widths['bones'])):
        c.reserve(512)
        start=c.pos;body={'native_index':i,'offset':start,'name':c.text('rigid name',True),'name_e':c.text('rigid English name',True),'bone':c.index('bones','rigid bone',True,True)}
        group,offset=c.enum(range(16),'rigid collision group');body['collision_group']={'offset':offset,'value':group}
        offset=c.pos;mask=c.integer(2,False,'rigid collision mask');body['collision_mask']={'offset':offset,'value':mask,'word_le_hex':data[offset:offset+2].hex()}
        shape,offset=c.enum((0,1,2),'rigid shape');body['shape']={'offset':offset,'value':shape}
        body['values']=c.floats(14,'rigid binary32 fields');mode,offset=c.enum((0,1,2),'rigid mode');body['mode']={'offset':offset,'value':mode};body['end_offset']=c.pos;bodies.append(body)
    end('rigid_bodies');c.close_deferred('rigid_bodies')
    joints=[]
    for i in range(begin('joints',105+2*c.widths['rigid_bodies'])):
        c.reserve(512)
        start=c.pos;joint={'native_index':i,'offset':start,'name':c.text('joint name',True),'name_e':c.text('joint English name',True)}
        mode,offset=c.enum((0,),'joint mode');joint['mode']={'offset':offset,'value':mode}
        joint['source']=c.index('rigid_bodies','joint source',True,True);joint['destination']=c.index('rigid_bodies','joint destination',True,True)
        joint['values']=c.floats(24,'joint binary32 fields');joint['end_offset']=c.pos;joints.append(joint)
    end('joints')
    if c.pos!=len(data):raise Refusal('unsupported trailing bytes or soft-body section')
    capsule={'format':'has_pmx20_native_physics_capsule_prototype_1','qualification':'UNQUALIFIED_SOURCE_CPU_ONLY','source_sha256':hashlib.sha256(data).hexdigest(),'source_bytes':len(data),'header':{'version_word_le_hex':version.hex(),'encoding':c.encoding,'encoding_byte':encoding,'global_bytes_le_hex':data[9:17].hex(),'additional_uv':uv,'index_widths':c.widths},'model_names':model_names,'rigid_f32_layout':[{'name':n,'word_offset':o,'words':w} for n,o,w in RIGID_F32_LAYOUT],'joint_f32_layout':[{'name':n,'word_offset':o,'words':w} for n,o,w in JOINT_F32_LAYOUT],'sections':sections,'bones':bones,'rigid_bodies':bodies,'joints':joints,'prefix_reference_policy':'Signed -1 is retained as absent where accepted by the declared layout-only field policy. Other negative and positive out-of-table references refuse. This does not establish valid skin, skeleton, material coverage or physical semantics.','f32_policy':'Bone and physics words are opaque exact little-endian binary32 hex; nonfinite words are explicitly classified and retained. No numerical physical-validity claim.','geometry_policy':'Strict bounded prefix layout walk only; geometry/morph names or payloads are not included in the capsule. Source SHA binds all input bytes.','budgets':{'operations_used':c.ops,'conservative_metadata_bytes_reserved':c.metadata_reserved,'string_bytes_used':c.string_bytes,'limits':{f.name:getattr(limits,f.name) for f in fields(Limits)}}}
    serialized=json.dumps(capsule,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode('utf-8')
    if len(serialized)>limits.metadata_bytes:raise Refusal('metadata byte budget')
    return capsule
