"""Hand-computed synthetic native binaries only; no private model input."""
import copy
import math
import struct
import sys
import unittest
import native_reader as N


class Bytes:
    def __init__(self, initial):self.data=bytearray(initial)
    def alloc(self, size):
        while len(self.data)%4:self.data.append(0)
        at=len(self.data);self.data.extend(b"\0"*size);return at
    def put(self, fmt, at, *values):struct.pack_into("<"+fmt,self.data,at,*values)
    def text(self, value):
        at=len(self.data);self.data.extend(value.encode("latin1")+b"\0");return at


def fixture():
    checksum=771
    md=Bytes(240);md.data[:4]=b"IDST";md.put("iI",4,49,checksum)
    bones=md.alloc(432);texture=md.alloc(64);skin=md.alloc(2);group=md.alloc(16);model=md.alloc(148);mesh=md.alloc(116)
    for i,name,parent in [(0,"root",-1),(1,"hand",0)]:
        at=bones+216*i;name_at=md.text(name);md.put("2i",at,name_at-at,parent)
    name_at=md.text("mat");md.put("i",texture,name_at-texture)
    group_name=md.text("tools");md.put("4i",group,group_name-group,1,1,model-group)
    md.data[model:model+10]=b"tools.dmx\0";md.put("4i",model+72,1,mesh-model,6,0)
    md.put("4i",mesh,0,model-mesh,6,0);md.put("8i",mesh+52,6,0,0,0,0,0,0,0)
    md.put("2i",156,2,bones);md.put("2i",204,1,texture);md.put("3i",220,1,1,skin);md.put("2i",232,1,group);md.put("I",76,len(md.data))
    vd=Bytes(64);vd.data[:4]=b"IDSV";vd.put("3I",4,4,checksum,1);vd.put("8I",16,6,0,0,0,0,0,0,0)
    fixups=vd.alloc(24);vertices=vd.alloc(6*48);tangents=vd.alloc(6*16)
    vd.put("3i",fixups,0,3,3);vd.put("3i",fixups+12,0,0,3)
    source_positions=[(0.,0.,0.),(1.,0.,0.),(0.,1.,0.),(2.,0.,0.),(3.,0.,0.),(2.,1.,0.)]
    for i,p in enumerate(source_positions):
        ids,weights,active=((0,0,0),(1.,0.,0.),1) if i<3 else ((1,0,0),(1.,0.,0.),1) if i<5 else ((1,0,0),(.25,.75,0.),2)
        vd.put("3f3BB3f3f2f",vertices+i*48,*weights,*ids,active,*p,0.,0.,1.,float(i%2),float(i//2)/3)
    vd.put("4I",48,2,fixups,vertices,tangents)
    tx=Bytes(36);replacement=tx.alloc(8);body=tx.alloc(8);choice=tx.alloc(8);lod=tx.alloc(12);txmesh=tx.alloc(9);sg=tx.alloc(25);txverts=tx.alloc(54);indices=tx.alloc(12);strips=tx.alloc(54)
    tx.put("IIHH6I",0,7,32,4,3,3,checksum,1,replacement,1,body)
    tx.put("2i",body,1,choice-body);tx.put("2i",choice,1,lod-choice);tx.put("2if",lod,1,txmesh-lod,0.)
    tx.put("2iB",txmesh,1,sg-txmesh,0);tx.put("6iB",sg,6,txverts-sg,6,indices-sg,2,strips-sg,2)
    for i in range(6):
        active=2 if i==2 else 1
        tx.put("4BH3B",txverts+i*9,0,1,2,active,i,0,1,2)
    tx.put("6H",indices,0,1,2,3,4,5)
    for i in range(2):
        at=strips+i*27;changes=tx.alloc(16);tx.put("2i",changes,0,0);tx.put("2i",changes+8,1,1)
        tx.put("4iHB2i",at,3,i*3,3,i*3,2,1,2,changes-at)
    return {"mdl":bytes(md.data),"vvd":bytes(vd.data),"vtx":bytes(tx.data)}, {"model":model,"mesh":mesh,"bones":bones,"fixups":fixups,"vertices":vertices,"sg":sg,"txverts":txverts,"indices":indices,"strips":strips}


class NativeReaderTests(unittest.TestCase):
    def setUp(self):self.files,self.at=fixture()
    def changed(self,kind,fmt,at,*values):
        raw=bytearray(self.files[kind]);struct.pack_into("<"+fmt,raw,at,*values);self.files[kind]=bytes(raw)
    def read(self):
        m=N.mdl(self.files['mdl']);v=N.vvd(self.files['vvd'],m['checksum'],len(m['bones']));t=N.vtx(self.files['vtx'],m,v);return m,v,t
    def test_hand_computed_complete_native_triangle_and_fixup_origins(self):
        m,v,t=self.read()
        self.assertEqual([r['source_row'] for r in v['lod0']],[3,4,5,0,1,2])
        self.assertEqual(v['lod0'][0]['position'],(2.,0.,0.))
        self.assertEqual(t['meshes'][0]['triangles'],[(0,1,2),(3,4,5)])
        self.assertEqual(v['lod0'][2]['weights'],{1:.25,0:.75})
    def test_strip_vertex_offset_not_added_to_group_indices(self):
        _,_,t=self.read();self.assertEqual(t['meshes'][0]['triangles'][1],(3,4,5))
    def test_explicit_adapter_transform_uv_and_winding(self):
        self.assertEqual(N.source_to_gltf((1.,2.,3.),.5),(.5,1.5,-1.))
        self.assertEqual(N.normal_to_gltf((0.,1.,0.)),(0.,0.,-1.))
        self.assertEqual(N.adapter_triangle((0,1,2)),(2,1,0))
    def test_mdl_wrong_version_rejected(self):
        self.changed('mdl','i',4,48)
        with self.assertRaises(N.FormatError):self.read()
    def test_mdl_declared_length_rejected(self):
        self.changed('mdl','I',76,5)
        with self.assertRaises(N.FormatError):self.read()
    def test_mdl_unaligned_vvd_byte_origin_rejected(self):
        self.changed('mdl','i',self.at['model']+84,1)
        with self.assertRaises(N.FormatError):self.read()
    def test_mdl_mesh_wrong_parent_rejected(self):
        self.changed('mdl','i',self.at['mesh']+4,0)
        with self.assertRaises(N.FormatError):self.read()
    def test_mdl_bone_cycle_rejected(self):
        self.changed('mdl','i',self.at['bones']+4,1)
        with self.assertRaises(N.FormatError):self.read()
    def test_vvd_bad_checksum_rejected(self):
        self.changed('vvd','I',8,772)
        with self.assertRaises(N.FormatError):self.read()
    def test_vvd_fixup_gap_or_overlap_rejected(self):
        self.changed('vvd','i',self.at['fixups']+16,1)
        with self.assertRaises(N.FormatError):self.read()
    def test_vvd_fixup_outside_table_rejected(self):
        self.changed('vvd','i',self.at['fixups']+4,5)
        with self.assertRaises(N.FormatError):self.read()
    def test_vvd_bad_native_bone_index_rejected(self):
        self.changed('vvd','B',self.at['vertices']+12,9)
        with self.assertRaises(N.FormatError):self.read()
    def test_vvd_nonfinite_uv_rejected(self):
        self.changed('vvd','f',self.at['vertices']+40,float('nan'))
        with self.assertRaises(N.FormatError):self.read()
    def test_nonunit_native_normal_observed_not_format_rejected(self):
        self.changed('vvd','3f',self.at['vertices']+28,0.,0.,2.)
        _,v,_=self.read();self.assertEqual(v['lod0'][3]['normal_length_squared'],4.)
    def test_nonfinite_normal_rejected(self):
        self.changed('vvd','f',self.at['vertices']+28,float('inf'))
        with self.assertRaises(N.FormatError):self.read()
    def test_vvd_nonunit_weights_rejected(self):
        self.changed('vvd','f',self.at['vertices'],.25)
        with self.assertRaises(N.FormatError):self.read()
    def test_vvd_offset_overrun_rejected(self):
        self.changed('vvd','I',56,len(self.files['vvd']))
        with self.assertRaises(N.FormatError):self.read()
    def test_vtx_bad_checksum_rejected(self):
        self.changed('vtx','I',16,772)
        with self.assertRaises(N.FormatError):self.read()
    def test_vtx_strip_or_quad_flag_rejected(self):
        self.changed('vtx','B',self.at['strips']+18,2)
        with self.assertRaises(N.FormatError):self.read()
    def test_vtx_restart_or_bad_group_index_rejected(self):
        self.changed('vtx','H',self.at['indices'],65535)
        with self.assertRaises(N.FormatError):self.read()
    def test_vtx_wrong_original_mesh_vertex_rejected(self):
        self.changed('vtx','H',self.at['txverts']+4,6)
        with self.assertRaises(N.FormatError):self.read()
    def test_vtx_overlapping_strip_index_range_rejected(self):
        self.changed('vtx','i',self.at['strips']+27+4,0)
        with self.assertRaises(N.FormatError):self.read()
    def test_vtx_table_truncation_rejected(self):
        self.files['vtx']=self.files['vtx'][:-3]
        with self.assertRaises(N.FormatError):self.read()
    def test_native_reader_imports_no_converter_or_native_module(self):
        self.assertFalse(any(n=='bpy' or n.startswith('SourceIO') or n=='numpy' for n in sys.modules))


if __name__=='__main__':unittest.main(verbosity=2)
