"""CPU-only prototype: exact VVD words recovered by an exported positive source ID.

No Blender/exporter API is exercised here. No files are written by this module.
Actual native exports, coordinate transport and bone/physics bindings remain unqualified.
"""
import copy
import hashlib
import json
import math
import struct
from dataclasses import dataclass

from vvd_normals import decode_lod0_normals

CARRIER = '_HAS_NATIVE_NORMAL_ID'
PROVENANCE = 'has_native_normal_identity_correction_1'
MAX_BYTES = 128*1024*1024
MAX_VERTICES = 200_000
UNIT_TOLERANCE = 2.5e-7


def require(ok,message):
    if not ok: raise ValueError(message)


def sha(raw): return hashlib.sha256(raw).hexdigest()


def typed_same(left,right):
    if type(left) is not type(right):return False
    if isinstance(left,dict):return left.keys()==right.keys() and all(typed_same(value,right[key]) for key,value in left.items())
    if isinstance(left,(list,tuple)):return len(left)==len(right) and all(typed_same(a,b) for a,b in zip(left,right))
    return left==right


def floats(words): return struct.unpack('<3f',struct.pack('<3I',*words))


def unit_words(words):
    require(len(words)==3 and all(type(v) is int and 0<=v<=0xffffffff for v in words),'Three uint32 normal words required')
    values=floats(words)
    require(all(math.isfinite(v) for v in values),'Nonfinite native normal refused')
    deviation=abs(math.sqrt(sum(v*v for v in values))-1.0)
    require(deviation<=UNIT_TOLERANCE,'Native unit length outside qualified tolerance; no normalization invented')
    return deviation


def signed_axes(axes):
    require(type(axes) in (list,tuple) and len(axes)==3 and all(type(v) is int for v in axes) and
            sorted(abs(v) for v in axes)==[1,2,3],'Explicit signed axis permutation required')
    order=[abs(v)-1 for v in axes]
    parity=(-1)**sum(order[i]>order[j] for i in range(3) for j in range(i+1,3))
    require(parity*math.prod(1 if v>0 else -1 for v in axes)==1,'Only proper signed rotations supported')
    return tuple(axes)


def transport_words(words,axes):
    axes=signed_axes(axes)
    unit_words(words)
    return tuple(words[abs(axis)-1] ^ (0x80000000 if axis<0 else 0) for axis in axes)


def split_word_halves(words):
    """Optional self-contained codec; positive integral F32 halves avoid -0 canonicalization."""
    require(len(words)==3 and all(type(v) is int and 0<=v<=0xffffffff for v in words),'Three uint32 words required')
    return tuple(float(v>>16) for v in words),tuple(float(v&65535) for v in words)


def join_word_halves(high,low):
    require(len(high)==len(low)==3,'Two three-component half vectors required')
    values=[]
    for value in (*high,*low):
        require(type(value) in (int,float) and math.isfinite(value) and 0<=value<=65535 and int(value)==value,
                'Finite integral unsigned16 halves required')
        require(not (value==0 and math.copysign(1.0,value)<0),'Negative-zero carrier half refused')
        values.append(int(value))
    return tuple((values[i]<<16)|values[i+3] for i in range(3))


@dataclass(frozen=True)
class NativeNormals:
    source_sha256: str
    checksum: int
    words: tuple
    source_bytes: bytes


def source_from_vvd(raw,expected_sha256,expected_checksum):
    require(type(raw) is bytes and sha(raw)==expected_sha256,'Exact pinned VVD bytes required')
    parsed=decode_lod0_normals(raw,expected_checksum=expected_checksum)
    offset=struct.unpack_from('<I',raw,56)[0]
    words=tuple(struct.unpack_from('<3I',raw,offset+index*48+28) for index in parsed['raw_vertex_indices'])
    for row in words: unit_words(row)
    return NativeNormals(expected_sha256,parsed['checksum'],words,raw)


def encode_ids(zero_based_indices):
    require(all(type(v) is int and 0<=v<MAX_VERTICES for v in zero_based_indices),'Bounded zero-based source indices required')
    return struct.pack('<'+'f'*len(zero_based_indices),*(v+1 for v in zero_based_indices))


def _no_duplicate_keys(pairs):
    value={}
    for key,item in pairs:
        require(key not in value,'Duplicate JSON key refused');value[key]=item
    return value


def parse_glb(raw):
    require(type(raw) is bytes and 28<=len(raw)<=MAX_BYTES,'Bounded GLB bytes required')
    require(struct.unpack_from('<4sII',raw)==(b'glTF',2,len(raw)),'Exact GLB2 header required')
    length,kind=struct.unpack_from('<I4s',raw,12)
    require(kind==b'JSON' and length%4==0 and 20+length+8<=len(raw),'JSON-first two-chunk GLB required')
    document=json.loads(raw[20:20+length].decode('utf-8'),object_pairs_hook=_no_duplicate_keys,
                        parse_constant=lambda value:(_ for _ in ()).throw(ValueError('Nonfinite JSON refused')))
    start=20+length;size,kind=struct.unpack_from('<I4s',raw,start)
    require(kind==b'BIN\0' and size%4==0 and start+8+size==len(raw),'One embedded BIN chunk required')
    binary=raw[start+8:]
    require(type(document) is dict and document.get('asset',{}).get('version')=='2.0','glTF2 asset required')
    buffers=document.get('buffers',[])
    require(len(buffers)==1 and type(buffers[0]) is dict and 'uri' not in buffers[0],'One embedded buffer required')
    declared=buffers[0].get('byteLength')
    require(type(declared) is int and declared<=len(binary)<=declared+3 and declared>=0,'Embedded buffer bounds differ')
    require(not any(binary[declared:]),'Unexpected BIN padding')
    forbidden={'KHR_draco_mesh_compression','EXT_meshopt_compression','KHR_mesh_quantization'}
    require(not forbidden.intersection(document.get('extensionsUsed',[])+document.get('extensionsRequired',[])),
            'Compressed or quantized profile refused')
    return document,binary


def pack_glb(document,binary):
    payload=json.dumps(document,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
    payload+=b' '*((-len(payload))%4)
    binary+=b'\0'*((-len(binary))%4)
    raw=struct.pack('<4sII',b'glTF',2,28+len(payload)+len(binary))+struct.pack('<I4s',len(payload),b'JSON')+payload+struct.pack('<I4s',len(binary),b'BIN\0')+binary
    require(len(raw)<=MAX_BYTES,'Candidate GLB exceeds budget')
    return raw


def _float_accessor(document,binary,index,kind):
    require(type(index) is int and 0<=index<len(document.get('accessors',[])),'Accessor identity out of range')
    accessor=document['accessors'][index]
    require(type(accessor.get('componentType')) is int and accessor['componentType']==5126 and accessor.get('type')==kind and
            accessor.get('normalized',False) is False and 'sparse' not in accessor,'Plain F32 accessor required')
    count=accessor.get('count');components={'SCALAR':1,'VEC3':3,'VEC4':4}[kind]
    require(type(count) is int and 1<=count<=MAX_VERTICES,'Bounded accessor count required')
    view_id=accessor.get('bufferView')
    require(type(view_id) is int and 0<=view_id<len(document.get('bufferViews',[])),'Embedded view required')
    view=document['bufferViews'][view_id]
    require(type(view.get('buffer')) is int and view['buffer']==0 and not view.get('extensions'),'Uncompressed embedded view required')
    offset=view.get('byteOffset',0);local=accessor.get('byteOffset',0);length=view.get('byteLength');stride=view.get('byteStride',components*4)
    require(all(type(v) is int for v in (offset,local,length,stride)) and min(offset,local,length)>=0 and
            offset%4==local%4==stride%4==0 and components*4<=stride<=252 and
            local+(count-1)*stride+components*4<=length and offset+length<=document['buffers'][0]['byteLength'],
            'Accessor/view range, alignment or stride invalid')
    return tuple(struct.unpack_from('<'+'f'*components,binary,offset+local+i*stride) for i in range(count))


def preservation_contract(before_raw,after_raw):
    """Type-exact non-NORMAL preservation only; use corrected_normal_contract separately."""
    before,old_bin=parse_glb(before_raw);after,new_bin=parse_glb(after_raw)
    require(new_bin[:len(old_bin)]==old_bin,'Existing BIN bytes changed')
    require(typed_same(after['accessors'][:len(before['accessors'])],before['accessors']) and
            typed_same(after['bufferViews'][:len(before['bufferViews'])],before['bufferViews']),'Existing accessor/view definitions changed')
    a=copy.deepcopy(before);b=copy.deepcopy(after)
    a.pop('accessors');b.pop('accessors');a.pop('bufferViews');b.pop('bufferViews')
    a['buffers'][0].pop('byteLength');b['buffers'][0].pop('byteLength')
    require(type(a.get('extras',{})) is dict and type(b.get('extras',{})) is dict,'Dictionary extras required')
    b.get('extras',{}).pop(PROVENANCE,None)
    if not b.get('extras',{}):b.pop('extras',None)
    if not a.get('extras',{}):a.pop('extras',None)
    require(len(a.get('meshes',[]))==len(b.get('meshes',[])),'Mesh count changed')
    for left,right in zip(a.get('meshes',[]),b.get('meshes',[])):
        require(len(left['primitives'])==len(right['primitives']),'Primitive count changed')
        for old,new in zip(left['primitives'],right['primitives']):
            old['attributes'].pop(CARRIER,None)
            require(type(new['attributes'].get('NORMAL')) is int and new['attributes']['NORMAL']>=len(before['accessors']),
                    'NORMAL must use an appended accessor')
            old['attributes'].pop('NORMAL');new['attributes'].pop('NORMAL')
    require(typed_same(a,b),'Non-NORMAL geometry, indices, UV/skin/morph/material/image/node data or unrelated metadata changed')
    return True


def corrected_normal_contract(output,native,verified_primitive_identity_order,axes):
    require(type(verified_primitive_identity_order) is dict and verified_primitive_identity_order,
            'Nonempty output identity relation required')
    document,binary=parse_glb(output)
    actual_keys=set()
    for mesh_index,mesh in enumerate(document.get('meshes',[])):
        for primitive_index,primitive in enumerate(mesh.get('primitives',[])):
            key=(mesh_index,primitive_index);actual_keys.add(key)
            require(key in verified_primitive_identity_order,'Missing output identity relation')
            attrs=primitive['attributes'];require(CARRIER not in attrs,'Temporary carrier not stripped')
            rows=_float_accessor(document,binary,attrs['NORMAL'],'VEC3')
            expected=verified_primitive_identity_order[key]
            require(type(expected) in (list,tuple) and all(type(i) is int and 1<=i<=len(native.words) for i in expected),
                    'Output source identities must be bounded integers')
            require(len(rows)==len(expected),'Output NORMAL count differs from source identity relation')
            actual=tuple(struct.unpack('<3I',struct.pack('<3f',*row)) for row in rows)
            wanted=tuple(transport_words(native.words[identity-1],axes) for identity in expected)
            require(typed_same(actual,wanted),'Output NORMAL words differ from exact source transport')
    require(actual_keys==verified_primitive_identity_order.keys(),'Output primitive relation differs')
    return True


def correct_glb(raw,native,expected_carrier_glb_sha256,expected_source_ids,axes,*,expected_native_sha256,verified_primitive_identity_order):
    """Return an unqualified derivative and scalar report; never mutate input bytes or files."""
    require(sha(raw)==expected_carrier_glb_sha256,'Exact carrier-export input required')
    require(isinstance(native,NativeNormals) and 1<=len(native.words)<=MAX_VERTICES,'Pinned native normal map required')
    derived=source_from_vvd(native.source_bytes,expected_native_sha256,native.checksum)
    require(native.source_sha256==expected_native_sha256 and type(native.checksum) is int and
            typed_same(native.words,derived.words),
            'Native source/map identity differs; inferred normals are not accepted')
    axes=signed_axes(axes)
    expected=set(expected_source_ids)
    require(len(expected)==len(expected_source_ids) and expected and all(type(i) is int and 1<=i<=len(native.words) for i in expected),
            'Exact expected source-identity coverage required')
    require(type(verified_primitive_identity_order) is dict and verified_primitive_identity_order and
            all(type(key) is tuple and len(key)==2 and all(type(v) is int and v>=0 for v in key) and
                type(ids) in (list,tuple) and ids and all(type(v) is int and v in expected for v in ids)
                for key,ids in verified_primitive_identity_order.items()),'Supplied per-primitive identity relation required')
    document,binary=parse_glb(raw);candidate=copy.deepcopy(document);new_bin=bytearray(binary)
    require(type(candidate.get('extras',{})) is dict and PROVENANCE not in candidate.get('extras',{}),'Provenance collision refused')
    seen=set();primitive_keys=set();primitive_count=0;normal_rows=0;appended={}
    for mesh_index,mesh in enumerate(candidate.get('meshes',[])):
        for primitive_index,primitive in enumerate(mesh.get('primitives',[])):
            require(type(primitive.get('mode',4)) is int and primitive.get('mode',4)==4 and not primitive.get('extensions'),'Uncompressed triangle primitives required')
            attrs=primitive.get('attributes',{})
            require(CARRIER in attrs and 'POSITION' in attrs and 'NORMAL' in attrs,'Complete original/carrier channels required')
            ids=_float_accessor(document,binary,attrs[CARRIER],'SCALAR')
            positions=_float_accessor(document,binary,attrs['POSITION'],'VEC3')
            old_normals=_float_accessor(document,binary,attrs['NORMAL'],'VEC3')
            require(len(ids)==len(positions)==len(old_normals),'Carrier/position/normal counts differ')
            require(all(all(math.isfinite(v) for v in row) for row in (*positions,*old_normals)),'Invalid existing geometry/normal values')
            words=[];decoded_ids=[]
            for row in ids:
                value=row[0]
                require(math.isfinite(value) and value==int(value) and 1<=value<=len(native.words),'Nonintegral, zero or out-of-range identity')
                identity=int(value);require(identity in expected,'Unexpected source identity')
                seen.add(identity);decoded_ids.append(identity);words.append(transport_words(native.words[identity-1],axes))
            primitive_key=(mesh_index,primitive_index);primitive_keys.add(primitive_key)
            require(primitive_key in verified_primitive_identity_order and
                    typed_same(tuple(decoded_ids),tuple(verified_primitive_identity_order[primitive_key])),
                    'Carrier identity order differs from supplied relation; coverage alone is insufficient')
            require(not any('NORMAL' in target or 'TANGENT' in target for target in primitive.get('targets',[])),
                    'Morph normal/tangent correction is outside this profile')
            if 'TANGENT' in attrs:
                tangents=_float_accessor(document,binary,attrs['TANGENT'],'VEC4')
                require(len(tangents)==len(words),'Tangent count differs')
                for tangent,word in zip(tangents,words):
                    require(all(math.isfinite(v) for v in tangent) and abs(tangent[3])==1 and
                            abs(math.sqrt(sum(v*v for v in tangent[:3]))-1)<=UNIT_TOLERANCE and
                            abs(sum(a*b for a,b in zip(tangent[:3],floats(word))))<=2e-5,
                            'Retained tangent is incompatible with corrected normal')
            key=(attrs[CARRIER],attrs['NORMAL'],axes)
            if key not in appended:
                offset=len(new_bin);payload=b''.join(struct.pack('<3I',*row) for row in words)
                require(len(new_bin)+len(payload)<=MAX_BYTES,'Candidate BIN exceeds budget')
                new_bin.extend(payload)
                view=len(candidate['bufferViews']);candidate['bufferViews'].append({'buffer':0,'byteOffset':offset,'byteLength':len(payload),'target':34962})
                index=len(candidate['accessors']);candidate['accessors'].append({'bufferView':view,'componentType':5126,'count':len(words),'type':'VEC3'})
                appended[key]=index;normal_rows+=len(words)
            attrs['NORMAL']=appended[key];del attrs[CARRIER];primitive_count+=1
    require(primitive_count>0 and seen==expected and primitive_keys==verified_primitive_identity_order.keys(),
            'Incomplete source-identity coverage; nearest-normal recovery forbidden')
    candidate['buffers'][0]['byteLength']=len(new_bin)
    candidate.setdefault('extras',{})[PROVENANCE]={'format':PROVENANCE,'source_vvd_sha256':native.source_sha256,
        'source_checksum':native.checksum,'carrier_glb_sha256':sha(raw),'source_identity_count':len(seen),
        'signed_axis_permutation':list(axes),'source_unit_conversion_changed':False,'six_foot_normalization_applied':False,
        'native_bone_and_physics_binding_requalification_required':True}
    output=pack_glb(candidate,bytes(new_bin));preservation_contract(raw,output)
    corrected_normal_contract(output,native,verified_primitive_identity_order,axes)
    return output,{'format':'has_native_normal_identity_prototype_report_1','status':'CANDIDATE_DERIVATIVE_UNQUALIFIED',
        'input_sha256':sha(raw),'output_sha256':sha(output),'source_vvd_sha256':native.source_sha256,
        'primitives':primitive_count,'source_identity_count':len(seen),'appended_normal_rows':normal_rows,
        'source_word_transport_exact':True,'all_original_BIN_bytes_preserved':True,'non_NORMAL_content_preserved':True,
        'identity_order_matches_supplied_manifest':True,'identity_manifest_independently_qualified':False,
        'native_runtime_or_artist_qualification':False,'six_foot_normalization_applied':False}
