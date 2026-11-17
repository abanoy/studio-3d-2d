import hashlib,itertools,json,re,struct,unittest
from dataclasses import replace
from synthetic_pmx import build_fixture
from pmx_native_physics import read_pmx20_physics,Limits,Refusal

def patch(raw,fields,name,word):
    field=fields[name];assert len(word)==field['bytes'];return raw[:field['offset']]+word+raw[field['end']:]

def mixed_widths(raw,expected,widths):
    """Repack independently authored field words, not reader output."""
    parts=[];starts={};end=0
    for name,field in expected['fields'].items():
        assert field['offset']==end;end=field['end'];kind=None
        if re.fullmatch(r'vertex.\d+.bone\d+',name):kind='bones'
        elif re.fullmatch(r'index.\d+',name):kind='vertices'
        elif re.fullmatch(r'material.\d+.(texture|sphere_texture)',name) or name=='material.1.toon':kind='textures'
        elif re.fullmatch(r'bone.\d+.(parent|tail|grant_parent|IK.target|IK.link\d+.target)',name):kind='bones'
        elif re.fullmatch(r'morph.\d+.group_morph',name):kind='morphs'
        elif re.fullmatch(r'morph.\d+.vertex',name):kind='vertices'
        elif re.fullmatch(r'morph.\d+.bone',name):kind='bones'
        elif re.fullmatch(r'morph.\d+.material',name):kind='materials'
        elif name=='display.bone.index' or name=='rigid.bone':kind='bones'
        elif name=='display.morph.index':kind='morphs'
        elif name in ('joint.source','joint.destination'):kind='rigid_bodies'
        word=raw[field['offset']:field['end']]
        if kind:word=field['value'].to_bytes(widths[kind],'little',signed=kind!='vertices')
        if name=='header':word=word[:11]+bytes(widths[k] for k in ('vertices','textures','materials','bones','morphs','rigid_bodies'))
        starts[name]=sum(map(len,parts));parts.append(word)
    assert end==len(raw)
    return b''.join(parts),starts

class FullPrefix(unittest.TestCase):
 def compare(self,raw,e):
    r=read_pmx20_physics(raw)
    self.assertEqual(r['source_sha256'],e['source_sha256']);self.assertEqual(r['source_bytes'],e['source_bytes'])
    aliases={'face_indices':'indices','rigid_bodies':'rigids'}
    for kind,section in r['sections'].items():
        k=aliases.get(kind,kind);self.assertEqual(section['count_offset'],e['sections'][k]);self.assertEqual(section['count'],e['counts'][k])
    for actual,want in zip(r['bones'],e['bones']):
        self.assertEqual((actual['offset'],actual['end_offset']),(want['offset'],want['end']))
        self.assertEqual(actual['name']['raw_hex'],want['name']['raw_hex']);self.assertEqual(actual['name']['text'],want['name']['decoded'])
        self.assertEqual(actual['flags']['value'],want['flags'])
    body=r['rigid_bodies'][0];joint=r['joints'][0]
    for actual,want in [(body,e['rigid']),(joint,e['joint'])]:
        self.assertEqual((actual['offset'],actual['end_offset']),(want['offset'],want['end']))
        self.assertEqual(actual['values']['offset'],want['F32_offset']);self.assertEqual(actual['values']['words_le_hex'],want['F32_words_le_hex'])
        self.assertEqual(actual['name']['raw_hex'],want['name']['raw_hex']);self.assertEqual(actual['name']['text'],want['name']['decoded'])
    self.assertEqual(body['values']['nonfinite_word_indices'],[13]);self.assertEqual(joint['values']['nonfinite_word_indices'],[23])
    return r
 def test_independent_full_prefix_matrix_all_width_encoding_uv_deform_tail_and_bone_layouts(self):
    matrix=itertools.product((1,2,4),(0,1),range(5),range(4),(False,True),(0,0x300,0x3f3f))
    for width,encoding,uv,deform,tail,flags in matrix:
        with self.subTest(width=width,encoding=encoding,uv=uv,deform=deform,tail=tail,flags=flags):
            raw,e=build_fixture(width,encoding,uv,deform,tail,flags);self.compare(raw,e)
 def test_unsigned_vertex_index_over127_with_signed_negative_bone(self):
    raw,e=build_fixture(vertex_count=130);r=self.compare(raw,e)
    self.assertEqual(e['face_indices'][-1],129);self.assertEqual(r['rigid_bodies'][0]['bone']['value'],-1)
 def test_mixed_index_width_roles_are_not_interchangeable(self):
    raw,e=build_fixture(bone_flags=0x3f3f,deform=3)
    roles=('vertices','textures','materials','bones','morphs','rigid_bodies')
    for offset in range(6):
        widths={role:(4 if i==offset else (1 if i%2==0 else 2)) for i,role in enumerate(roles)}
        mixed,starts=mixed_widths(raw,e,widths);r=read_pmx20_physics(mixed)
        self.assertEqual(r['header']['index_widths'],widths)
        self.assertEqual(r['rigid_bodies'][0]['offset'],starts['rigid.name.length']);self.assertEqual(r['joints'][0]['offset'],starts['joint.name.length'])
        self.assertEqual(r['rigid_bodies'][0]['values']['words_le_hex'],e['rigid']['F32_words_le_hex'])
        self.assertEqual(r['joints'][0]['values']['words_le_hex'],e['joint']['F32_words_le_hex'])
 def test_empty_morph_table_and_single_display_tag(self):
    raw,e=build_fixture(morph_types=());r=self.compare(raw,e);self.assertEqual(r['sections']['morphs']['count'],0)
 def test_all_full_prefix_truncation_points_refuse(self):
    raw,e=build_fixture(index_size=4,encoding=0,additional_uv=4,deform=3,bone_flags=0x3f3f)
    for end in range(len(raw)):
        with self.subTest(end=end),self.assertRaises(Refusal):read_pmx20_physics(raw[:end])
 def test_unknown_selectors_never_guess_record_sizes(self):
    raw,e=build_fixture(bone_flags=0x3f3f);f=e['fields']
    bad=[('vertex.0.deform',4),('material.0.flags',32),('material.0.sphere_mode',4),('material.0.shared_toon',2),('material.0.toon',10),('bone.0.IK.link0.limited',2),('morph.0.category',5),('morph.0.type',9),('morph.8.operation',2),('display.special',2),('display.bone.tag',2)]
    for name,value in bad:
        with self.subTest(field=name),self.assertRaises(Refusal):read_pmx20_physics(patch(raw,f,name,bytes([value])))
 def test_prefix_reference_ranges_are_checked(self):
    raw,e=build_fixture(bone_flags=0x3f3f);f=e['fields']
    bad=[('vertex.0.bone0',-2),('vertex.0.bone0',2),('index.0',3),('material.0.texture',1),('bone.0.parent',2),('bone.0.grant_parent',2),('bone.0.IK.target',2),('morph.0.group_morph',9),('morph.1.vertex',3),('morph.2.bone',2),('morph.8.material',2),('display.bone.index',2),('display.morph.index',9)]
    for name,value in bad:
        word=value.to_bytes(1,'little',signed=not name.startswith('index.') and not name.endswith('.vertex'))
        with self.subTest(field=name,value=value),self.assertRaises(Refusal):read_pmx20_physics(patch(raw,f,name,word))
 def test_nested_counts_and_aggregates_are_bounded(self):
    raw,e=build_fixture(bone_flags=0x3f3f);f=e['fields']
    for name in ['bone.0.IK.links','morph.0.offset_count','display.elements']:
        for value in [-1,2**31-1]:
            with self.subTest(field=name,value=value),self.assertRaises(Refusal):read_pmx20_physics(patch(raw,f,name,struct.pack('<i',value)))
    for limits in [replace(Limits(),ik_links=1),replace(Limits(),morph_offsets=8),replace(Limits(),display_elements=1)]:
        with self.assertRaises(Refusal):read_pmx20_physics(raw,limits)
 def test_physics_refs_remain_strict_at_each_width(self):
    for width in (1,2,4):
        for field in ('bone_ref','rigid_ref'):
            for value in (-2,2):
                raw,e=build_fixture(index_size=width,**{field:value})
                with self.assertRaises(Refusal):read_pmx20_physics(raw)
 def test_unknown_joint_modes_and_bone_flags_refuse(self):
    for mode in (-1,1,127):
        raw,e=build_fixture(joint_mode=mode)
        with self.assertRaises(Refusal):read_pmx20_physics(raw)
    for flag in (0x40,0x80,0x4000,0x8000):
        raw,e=build_fixture(bone_flags=flag)
        with self.assertRaises(Refusal):read_pmx20_physics(raw)
 def test_material_face_count_remains_count_of_indices(self):
    raw,e=build_fixture();f=e['fields']
    for name,value in [('indices.count',2),('material.0.surface_indices',-1),('material.0.surface_indices',1),('material.0.surface_indices',6)]:
        with self.assertRaises(Refusal):read_pmx20_physics(patch(raw,f,name,struct.pack('<i',value)))
 def test_bone_optional_payloads_and_signedzero_retained(self):
    raw,e=build_fixture(bone_flags=0x3f3f);r=read_pmx20_physics(raw);b=r['bones'][0]
    self.assertIn('grant',b);self.assertEqual(len(b['grant']['influence']['words_le_hex']),1)
    self.assertEqual(len(b['local_axes']['words_le_hex']),6);self.assertEqual(len(b['fixed_axis']['words_le_hex']),3)
    self.assertEqual(len(b['ik']['links']),2);self.assertIn('angle_bounds',b['ik']['links'][0]);self.assertNotIn('angle_bounds',b['ik']['links'][1])
    self.assertEqual(b['location']['words_le_hex'][1],'00000080')
 def test_field_layout_word_offsets_cover_exact_physics_words(self):
    raw,e=build_fixture();r=read_pmx20_physics(raw)
    for key,total in [('rigid_f32_layout',14),('joint_f32_layout',24)]:
        seen=[]
        for field in r[key]:seen.extend(range(field['word_offset'],field['word_offset']+field['words']))
        self.assertEqual(seen,list(range(total)))

if __name__=='__main__':unittest.main()
