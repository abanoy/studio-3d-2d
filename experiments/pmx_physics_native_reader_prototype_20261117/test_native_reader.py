from dataclasses import replace
import hashlib,json,random,struct,unittest
from pathlib import Path
from pmx_native_physics import read_pmx20_physics,Limits,Refusal
HERE=Path(__file__).resolve().parent
ORACLE=json.loads((HERE/'MANUAL_FIXTURE_EXPECTATIONS.json').read_bytes())
RAW=bytes.fromhex(ORACLE['complete_hex'])

def altered(offset,word):
    return RAW[:offset]+word+RAW[offset+len(word):]

class ManualOracle(unittest.TestCase):
 def test_independent_manual_oracle_source_join(self):
  r=read_pmx20_physics(RAW)
  self.assertEqual(r['source_sha256'],ORACLE['sha256']);self.assertEqual(r['source_bytes'],339)
  self.assertEqual(r['sections']['rigid_bodies']['count_offset'],145)
  self.assertEqual(r['sections']['joints']['count_offset'],223)
  self.assertEqual([(b['offset'],b['end_offset']) for b in r['bones']],[(53,95),(95,137)])
  body=r['rigid_bodies'][0];joint=r['joints'][0]
  self.assertEqual((body['offset'],body['end_offset']),(149,223));self.assertEqual((joint['offset'],joint['end_offset']),(227,339))
  self.assertEqual(body['values']['words_le_hex'],ORACLE['rigid0']['F32_words_le_hex'])
  self.assertEqual(joint['values']['words_le_hex'],ORACLE['joint0']['F32_words_le_hex'])
 def test_duplicate_and_empty_names_preserved(self):
  r=read_pmx20_physics(RAW)
  self.assertEqual([b['native_index'] for b in r['bones']],[0,1]);self.assertEqual([b['name']['text'] for b in r['bones']],['dup','dup'])
  self.assertEqual([b['name']['raw_hex'] for b in r['bones']],['647570']*2)
  self.assertEqual([b['name_e']['text'] for b in r['bones']],['',''])
 def test_absent_index_and_high_mask_word_preserved(self):
  r=read_pmx20_physics(RAW);body=r['rigid_bodies'][0];joint=r['joints'][0]
  self.assertEqual(body['bone']['value'],1);self.assertEqual(body['bone']['word_le_hex'],'01')
  self.assertEqual(body['collision_mask']['value'],32769);self.assertEqual(body['collision_mask']['word_le_hex'],'0180')
  self.assertEqual(joint['destination']['value'],-1);self.assertEqual(joint['destination']['word_le_hex'],'ff')
  r=read_pmx20_physics(altered(161,b'\xff'));self.assertEqual(r['rigid_bodies'][0]['bone']['value'],-1)
 def test_all_truncation_points_refuse_without_tolerant_defaults(self):
  for end in range(len(RAW)):
   with self.subTest(end=end),self.assertRaises(Refusal):read_pmx20_physics(RAW[:end])
 def test_trailing_bytes_or_soft_body_count_refuse(self):
  for suffix in [b'\x00',b'\x00'*4,b'PMX ']:
   with self.assertRaisesRegex(Refusal,'trailing'):read_pmx20_physics(RAW+suffix)
 def test_unknown_header_profiles_refuse(self):
  variants=[altered(0,b'PMXx'),altered(4,struct.pack('<f',2.1)),altered(8,b'\x09'),altered(9,b'\x02'),altered(10,b'\x05')]
  variants += [altered(offset,b'\x03') for offset in range(11,17)]
  for raw in variants:
   with self.assertRaises(Refusal):read_pmx20_physics(raw)
 def test_all_table_counts_negative_or_excessive_refuse(self):
  offsets=[33,37,41,45,49,137,141,145,223]
  for offset in offsets:
   for count in [-1,2**31-1]:
    with self.subTest(offset=offset,count=count),self.assertRaises(Refusal):read_pmx20_physics(altered(offset,struct.pack('<i',count)))
 def test_string_length_and_utf_strict(self):
  for raw in [altered(17,struct.pack('<i',-1)),altered(17,struct.pack('<i',2**31-1)),altered(57,b'\xff'),altered(9,b'\x00')]:
   with self.assertRaises(Refusal):read_pmx20_physics(raw)
 def test_ref_minus_two_not_collapsed_and_positive_range_checked(self):
  for offset,maxvalue in [(76,2),(161,2),(241,1),(242,1)]:
   for byte in [254,maxvalue]:
    with self.subTest(offset=offset,byte=byte),self.assertRaises(Refusal):read_pmx20_physics(altered(offset,bytes([byte])))
 def test_unknown_bone_and_physics_selectors_refuse(self):
  for offset,word in [(81,b'\x40\x00'),(162,b'\x10'),(165,b'\x03'),(222,b'\x03'),(240,b'\x01')]:
   with self.assertRaises(Refusal):read_pmx20_physics(altered(offset,word))
 def test_masks_do_not_lose_unsigned_high_bit(self):
  for value in [0,0x8000,0xffff]:
   r=read_pmx20_physics(altered(163,struct.pack('<H',value)))
   self.assertEqual(r['rigid_bodies'][0]['collision_mask']['value'],value)
 def test_raw_f32_signedzero_subnormal_nan_inf_preserved_and_classified(self):
  words=['00000080','01000000','0100c07f','0000807f','000080ff']
  for word in words:
   r=read_pmx20_physics(altered(166,bytes.fromhex(word)));values=r['rigid_bodies'][0]['values']
   self.assertEqual(values['words_le_hex'][0],word)
   self.assertEqual(0 in values['nonfinite_word_indices'],word in words[2:])
   json.dumps(r,allow_nan=False)
 def test_bone_raw_location_words_preserved(self):
  raw=altered(64,bytes.fromhex('00000080'));r=read_pmx20_physics(raw)
  self.assertEqual(r['bones'][0]['location']['words_le_hex'][0],'00000080')
 def test_source_hash_binds_each_binary_change(self):
  r=read_pmx20_physics(altered(163,b'\x00\x80'))
  self.assertEqual(r['source_sha256'],hashlib.sha256(altered(163,b'\x00\x80')).hexdigest());self.assertNotEqual(r['source_sha256'],ORACLE['sha256'])
 def test_immutable_bytes_only(self):
  for value in [bytearray(RAW),memoryview(RAW),None,'PMX ']:
   with self.assertRaises(Refusal):read_pmx20_physics(value)
 def test_limits_are_typed_bounded_and_cannot_widen(self):
  for limits in [None,{},replace(Limits(),bones=True),replace(Limits(),bones=-1),replace(Limits(),bones=4097)]:
   with self.assertRaises(Refusal):read_pmx20_physics(RAW,limits)
 def test_small_resource_budgets_refuse_without_partial_result(self):
  for limits in [replace(Limits(),source_bytes=338),replace(Limits(),string_bytes=2),replace(Limits(),total_string_bytes=2),replace(Limits(),retained_name_utf8_bytes=2),replace(Limits(),operations=1),replace(Limits(),metadata_bytes=1),replace(Limits(),bones=1),replace(Limits(),rigid_bodies=0),replace(Limits(),joints=0)]:
   with self.subTest(limits=limits),self.assertRaises(Refusal):read_pmx20_physics(RAW,limits)
 def test_exact_count_limits_can_pass(self):
  r=read_pmx20_physics(RAW,replace(Limits(),bones=2,rigid_bodies=1,joints=1,source_bytes=339))
  self.assertEqual(len(r['rigid_bodies']),1)
 def test_deterministic_single_byte_fuzz_is_total_or_refusal(self):
  rng=random.Random(20261117)
  for _ in range(1000):
   raw=bytearray(RAW);raw[rng.randrange(len(raw))]=rng.randrange(256)
   try:r=read_pmx20_physics(bytes(raw))
   except Refusal:continue
   self.assertEqual(r['source_sha256'],hashlib.sha256(raw).hexdigest())
   json.dumps(r,allow_nan=False)
 def test_capsule_retains_unqualified_scope(self):
  r=read_pmx20_physics(RAW)
  self.assertEqual(r['qualification'],'UNQUALIFIED_SOURCE_CPU_ONLY');self.assertIn('layout walk only',r['geometry_policy'])
  self.assertIn('No numerical physical-validity claim',r['f32_policy'])

if __name__=='__main__':unittest.main()
