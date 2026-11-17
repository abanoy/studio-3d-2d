"""Synthetic VVD/GLB bytes only. No Blender, installed exporter, native files or runtime."""
import copy
from dataclasses import replace
import math
import struct
import unittest

import normal_identity_carrier as C


def vvd(normals=None):
    normals=normals or [((-0.0 if i==0 else 0.0),math.sin(a),math.cos(a)) for i,a in enumerate((0,0,.001,.002,.003,.004,.005,.006))]
    count=len(normals)
    raw=bytearray(struct.pack('<4s15I',b'IDSV',4,17,1,count,*([0]*7),0,0,64,0)+b'\0'*(count*48))
    for i,row in enumerate(normals): struct.pack_into('<3f',raw,64+i*48+28,*row)
    return bytes(raw)


def fixture():
    binary=bytearray();views=[];accessors=[]
    def add(body,component,kind,count):
        binary.extend(b'\0'*((-len(binary))%4));offset=len(binary);binary.extend(body)
        view=len(views);views.append({'buffer':0,'byteOffset':offset,'byteLength':len(body)})
        index=len(accessors);accessors.append({'bufferView':view,'componentType':component,'count':count,'type':kind})
        return index
    def f(values):return struct.pack('<'+'f'*len(values),*values)
    n=8
    attrs={'POSITION':add(f([0.,0.,0.]*n),5126,'VEC3',n),
           'NORMAL':add(f([0.,1.,0.]*n),5126,'VEC3',n),
           'TEXCOORD_0':add(f([.5,.5]*n),5126,'VEC2',n),
           'JOINTS_0':add(bytes([0,0,0,0]*n),5121,'VEC4',n),
           'WEIGHTS_0':add(f([1.,0.,0.,0.]*n),5126,'VEC4',n),
           'TANGENT':add(f([1.,0.,0.,1.]*n),5126,'VEC4',n),
           C.CARRIER:add(C.encode_ids(list(range(n))),5126,'SCALAR',n)}
    indices=add(struct.pack('<'+'H'*(n*3),*(i for i in range(n) for _ in range(3))),5123,'SCALAR',n*3)
    morph=add(f([.01,0.,0.]*n),5126,'VEC3',n)
    bind=add(f([1.,0.,0.,0.,0.,1.,0.,0.,0.,0.,1.,0.,0.,0.,0.,1.]),5126,'MAT4',1)
    document={'asset':{'version':'2.0','generator':'synthetic normal carrier CPU fixture'},
              'buffers':[{'byteLength':len(binary)}],'bufferViews':views,'accessors':accessors,
              'meshes':[{'name':'eight coincident source identities','weights':[.25],
                         'primitives':[{'attributes':attrs,'indices':indices,'material':0,'targets':[{'POSITION':morph}]}]}],
              'skins':[{'joints':[1],'inverseBindMatrices':bind}],
              'nodes':[{'mesh':0,'skin':0,'name':'mesh','translation':[1,2,3]},{'name':'bone'}],
              'materials':[{'pbrMetallicRoughness':{'baseColorFactor':[.2,.3,.4,1.]}}],
              'scenes':[{'nodes':[0,1]}],'scene':0,'extras':{'owner_metadata':{'retained':True,'number':1.5}}}
    return C.pack_glb(document,bytes(binary))


class CarrierTests(unittest.TestCase):
    def setUp(self):
        self.raw_vvd=vvd();self.native=C.source_from_vvd(self.raw_vvd,C.sha(self.raw_vvd),17);self.raw=fixture()

    def correct(self,raw=None,native=None,ids=None,axes=(1,3,-2),expected_source=None):
        raw=self.raw if raw is None else raw;native=self.native if native is None else native
        return C.correct_glb(raw,native,C.sha(raw),list(range(1,9)) if ids is None else ids,axes,
                             expected_native_sha256=self.native.source_sha256 if expected_source is None else expected_source,
                             verified_primitive_identity_order={(0,0):list(range(1,9))})

    def mutate(self,change):
        doc,binary=C.parse_glb(self.raw);binary=bytearray(binary);change(doc,binary)
        return C.pack_glb(doc,bytes(binary))

    def test_eight_ambiguous_word_classes_recovered_by_identity(self):
        self.assertEqual(len(set(self.native.words)),8)
        output,report=self.correct()
        doc,binary=C.parse_glb(output);attrs=doc['meshes'][0]['primitives'][0]['attributes']
        self.assertNotIn(C.CARRIER,attrs)
        expected=[C.transport_words(row,(1,3,-2)) for row in self.native.words]
        accessor=doc['accessors'][attrs['NORMAL']];view=doc['bufferViews'][accessor['bufferView']]
        actual=[struct.unpack_from('<3I',binary,view['byteOffset']+i*12) for i in range(8)]
        self.assertEqual(actual,expected)
        self.assertEqual(len(set(actual)),8)
        self.assertEqual(actual[0][0],0x80000000)
        self.assertEqual(actual[1][0],0)
        self.assertEqual(report['status'],'CANDIDATE_DERIVATIVE_UNQUALIFIED')
        self.assertFalse(report['native_runtime_or_artist_qualification'])

    def test_geometry_skin_uv_morph_and_metadata_preservation(self):
        before_doc,before_bin=C.parse_glb(self.raw);original_bytes=self.raw
        output,report=self.correct();after_doc,after_bin=C.parse_glb(output)
        self.assertEqual(before_bin,after_bin[:len(before_bin)])
        self.assertEqual(before_doc['skins'],after_doc['skins'])
        self.assertEqual(before_doc['nodes'],after_doc['nodes'])
        self.assertEqual(before_doc['materials'],after_doc['materials'])
        self.assertEqual(before_doc['accessors'],after_doc['accessors'][:len(before_doc['accessors'])])
        self.assertEqual(before_doc['meshes'][0]['primitives'][0]['targets'],after_doc['meshes'][0]['primitives'][0]['targets'])
        self.assertEqual(before_doc['extras']['owner_metadata'],after_doc['extras']['owner_metadata'])
        self.assertEqual(self.raw,original_bytes)
        self.assertTrue(C.preservation_contract(self.raw,output))
        self.assertFalse(after_doc['extras'][C.PROVENANCE]['six_foot_normalization_applied'])

    def test_positive_one_based_ids_survive_f32_exactly(self):
        values=struct.unpack('<4f',C.encode_ids([0,1,65535,199999]))
        self.assertEqual(values,(1.,2.,65536.,200000.))
        for bad in ([-1],[200000],[True],[1.5]):
            with self.assertRaises(ValueError):C.encode_ids(bad)

    def test_optional_half_codec_preserves_all_word_bits(self):
        words=(0x80000000,0x3f800001,0xffffffff)
        high,low=C.split_word_halves(words)
        high=struct.unpack('<3f',struct.pack('<3f',*high));low=struct.unpack('<3f',struct.pack('<3f',*low))
        self.assertEqual(C.join_word_halves(high,low),words)
        self.assertNotEqual(int(struct.unpack('<f',struct.pack('<f',float(words[1])))[0]),words[1])
        for bad in ((-0.0,0.,0.),(65536.,0.,0.),(1.5,0.,0.),(float('nan'),0.,0.)):
            with self.assertRaises(ValueError):C.join_word_halves(bad,low)

    def test_source_vvd_hash_checksum_and_inferred_map_refused(self):
        with self.assertRaises(ValueError):C.source_from_vvd(self.raw_vvd,'0'*64,17)
        with self.assertRaises(ValueError):C.source_from_vvd(self.raw_vvd,C.sha(self.raw_vvd),18)
        with self.assertRaises(ValueError):self.correct(expected_source='0'*64)
        altered=replace(self.native,words=(self.native.words[1],)+self.native.words[1:])
        with self.assertRaises(ValueError):self.correct(native=altered)
        with self.assertRaises(ValueError):C.correct_glb(self.raw,self.native,'0'*64,list(range(1,9)),(1,3,-2),expected_native_sha256=self.native.source_sha256,verified_primitive_identity_order={(0,0):list(range(1,9))})

    def test_nonfinite_zero_and_nonunit_source_normals_refused(self):
        for row in ((float('nan'),0.,1.),(float('inf'),0.,1.),(0.,0.,0.),(0.,0.,2.)):
            source=vvd([row])
            with self.assertRaises(ValueError):C.source_from_vvd(source,C.sha(source),17)

    def test_non_permutation_nonuniform_and_mirrored_transport_refused(self):
        for axes in ((1,2,2),(1,2,-3),(1.,3,-2),(1,3,-.5),(1,2)):
            with self.assertRaises(ValueError):self.correct(axes=axes)

    def test_missing_fractional_zero_or_unknown_ids_refused(self):
        def alter(value):
            def mutate(doc,binary):
                idx=doc['meshes'][0]['primitives'][0]['attributes'][C.CARRIER]
                view=doc['bufferViews'][doc['accessors'][idx]['bufferView']]
                struct.pack_into('<f',binary,view['byteOffset'],value)
            return self.mutate(mutate)
        for value in (0.,1.5,9.,float('nan'),float('inf'),-0.0):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):self.correct(raw=alter(value))
        def remove(doc,binary):doc['meshes'][0]['primitives'][0]['attributes'].pop(C.CARRIER)
        with self.assertRaises(ValueError):self.correct(raw=self.mutate(remove))

    def test_exact_coverage_no_nearest_fallback(self):
        for ids in ([1,2,3,4,5,6,7],[1,2,3,4,5,6,7,8,8],[1,2,3,4,5,6,7,9]):
            with self.assertRaises(ValueError):self.correct(ids=ids)
        def duplicate(doc,binary):
            idx=doc['meshes'][0]['primitives'][0]['attributes'][C.CARRIER]
            view=doc['bufferViews'][doc['accessors'][idx]['bufferView']]
            struct.pack_into('<f',binary,view['byteOffset']+7*4,7.)
        with self.assertRaises(ValueError):self.correct(raw=self.mutate(duplicate))

    def test_morph_normal_and_incompatible_tangent_refused(self):
        def normal_target(doc,binary):doc['meshes'][0]['primitives'][0]['targets'][0]['NORMAL']=0
        with self.assertRaises(ValueError):self.correct(raw=self.mutate(normal_target))
        def tangent(doc,binary):
            idx=doc['meshes'][0]['primitives'][0]['attributes']['TANGENT']
            view=doc['bufferViews'][doc['accessors'][idx]['bufferView']]
            struct.pack_into('<4f',binary,view['byteOffset'],0.,1.,0.,1.)
        with self.assertRaises(ValueError):self.correct(raw=self.mutate(tangent))

    def test_sparse_quantized_collision_and_bounds_refused(self):
        mutations=[lambda d,b:d['accessors'][d['meshes'][0]['primitives'][0]['attributes'][C.CARRIER]].update(sparse={}),
                   lambda d,b:d.update(extensionsUsed=['KHR_mesh_quantization']),
                   lambda d,b:d['extras'].update({C.PROVENANCE:{}}),
                   lambda d,b:d['bufferViews'][0].update(byteLength=999999),
                   lambda d,b:d['accessors'][0].update(componentType=5126.0),
                   lambda d,b:d['bufferViews'][0].update(buffer=False)]
        for change in mutations:
            with self.assertRaises(ValueError):self.correct(raw=self.mutate(change))

    def test_independent_preservation_contract_rejects_other_edits(self):
        output,_=self.correct();doc,binary=C.parse_glb(output)
        modified=bytearray(binary);modified[0]^=1
        with self.assertRaises(ValueError):C.preservation_contract(self.raw,C.pack_glb(doc,bytes(modified)))
        for mutate in (lambda d:d['nodes'][0].update(translation=[9,2,3]),
                       lambda d:d['meshes'][0]['primitives'][0]['attributes'].update(TEXCOORD_0=0),
                       lambda d:d['meshes'][0]['primitives'][0].update(targets=[]),
                       lambda d:d['skins'][0].update(joints=[0]),
                       lambda d:d['extras']['owner_metadata'].update(retained=False)):
            bad=copy.deepcopy(doc);mutate(bad)
            with self.assertRaises(ValueError):C.preservation_contract(self.raw,C.pack_glb(bad,binary))

    def test_type_only_metadata_index_and_accessor_changes_refused(self):
        output,_=self.correct();doc,binary=C.parse_glb(output)
        for mutate in (lambda d:d['extras']['owner_metadata'].update(retained=1),
                       lambda d:d['meshes'][0]['primitives'][0].update(indices=float(d['meshes'][0]['primitives'][0]['indices'])),
                       lambda d:d['accessors'][0].update(count=8.0),
                       lambda d:d['nodes'][0].update(skin=False)):
            bad=copy.deepcopy(doc);mutate(bad)
            with self.assertRaises(ValueError):C.preservation_contract(self.raw,C.pack_glb(bad,binary))

    def test_complete_set_permutation_is_not_correspondence(self):
        def swap(doc,binary):
            idx=doc['meshes'][0]['primitives'][0]['attributes'][C.CARRIER]
            view=doc['bufferViews'][doc['accessors'][idx]['bufferView']]
            struct.pack_into('<2f',binary,view['byteOffset'],2.,1.)
        with self.assertRaisesRegex(ValueError,'identity order'):self.correct(raw=self.mutate(swap))
        with self.assertRaises(ValueError):C.correct_glb(self.raw,self.native,C.sha(self.raw),list(range(1,9)),(1,3,-2),expected_native_sha256=self.native.source_sha256,verified_primitive_identity_order={})

    def test_output_normal_storage_and_words_have_separate_guard(self):
        output,_=self.correct();doc,binary=C.parse_glb(output)
        normal_index=doc['meshes'][0]['primitives'][0]['attributes']['NORMAL']
        for relation in ({},{(0,0):[True]+list(range(2,9))},{(0,0):[0]+list(range(2,9))}):
            with self.assertRaises(ValueError):C.corrected_normal_contract(output,self.native,relation,(1,3,-2))
        for mutate in (lambda d:d['meshes'][0]['primitives'][0]['attributes'].update(NORMAL=99999),
                       lambda d:d['accessors'][normal_index].update(type='SCALAR',count=1),
                       lambda d:d['bufferViews'][-1].update(byteOffset=len(binary)+4)):
            bad=copy.deepcopy(doc);mutate(bad);raw=C.pack_glb(bad,binary)
            with self.assertRaises(ValueError):C.corrected_normal_contract(raw,self.native,{(0,0):list(range(1,9))},(1,3,-2))
        bad=bytearray(binary);bad[doc['bufferViews'][-1]['byteOffset']]^=1
        raw=C.pack_glb(doc,bytes(bad))
        self.assertTrue(C.preservation_contract(self.raw,raw))
        with self.assertRaises(ValueError):C.corrected_normal_contract(raw,self.native,{(0,0):list(range(1,9))},(1,3,-2))

    def test_unsupported_glb_chunk_header_and_accessor_count_refused(self):
        with self.assertRaises(ValueError):C.parse_glb(self.raw[:-4])
        broken=bytearray(self.raw);struct.pack_into('<I',broken,4,1)
        with self.assertRaises(ValueError):C.parse_glb(bytes(broken))
        def count(doc,binary):
            idx=doc['meshes'][0]['primitives'][0]['attributes'][C.CARRIER]
            doc['accessors'][idx]['count']=7
        with self.assertRaises(ValueError):self.correct(raw=self.mutate(count))


if __name__=='__main__':unittest.main()
