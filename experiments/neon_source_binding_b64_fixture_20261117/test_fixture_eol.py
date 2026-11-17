"""Independent authored golden-byte checks; decoded GLB stays in RAM."""
from pathlib import Path
import base64,hashlib,json,re,struct,unittest
HERE=Path(__file__).resolve().parent
GOLDEN_SHA='39637fa34e53c81708329ab963659e8100a285a92e25a22a92ab5e708c0154c1'
BAD_SHA='95e0c8785860cfce8ad34a60ff58feef6c65d22ea6a6d318d9523ddfdd0ff934'
OLD=b'GOLDEN_GLB.replace("\\n", "")'
NEW=b'GOLDEN_GLB.replace("\\r", "").replace("\\n", "")'
def literal(raw):
 match=re.search(rb'const\s+GOLDEN_GLB\s*:?=\s*"""(.*?)"""',raw,re.S)
 if match is None:raise ValueError('Exact authored literal missing')
 return match[1]
def decode(payload):return base64.b64decode(payload.replace(b'\r',b'').replace(b'\n',b''),validate=True)
def digest(raw):return hashlib.sha256(raw).hexdigest()
class FixtureEOL(unittest.TestCase):
 def setUp(self):
  self.original=(HERE/'original-source_bone_bindings_unit.gd').read_bytes();self.proposed=(HERE/'source_bone_bindings_unit.proposed.gd').read_bytes();self.payload=literal(self.original)
 def test_exact_one_expression_inverse_preserves_every_other_source_byte(self):
  self.assertEqual(self.original.count(OLD),1);self.assertEqual(self.proposed.count(NEW),1);self.assertEqual(self.proposed.replace(NEW,OLD,1),self.original)
 def test_main52_and_candidate375_sources_differ_only_by_CRLF(self):
  main=(HERE/'main52-source_bone_bindings_unit.gd').read_bytes();self.assertEqual(main,self.original.replace(b'\r\n',b'\n'))
 def test_root_supplied375_Git_blob_is_exact_main52_LF_body(self):
  blob=(HERE/'original-candidate-git-blob.gd').read_bytes();self.assertEqual(blob,(HERE/'main52-source_bone_bindings_unit.gd').read_bytes());self.assertEqual(blob,self.original.replace(b'\r\n',b'\n'));self.assertEqual(hashlib.sha1(b'blob '+str(len(blob)).encode()+b'\0'+blob).hexdigest(),'66f6af2b9236aefcab46ba29c4e7b63b01e7e144')
 def test_independent_hardcoded_golden9360_bytes_and_container_header(self):
  raw=decode(self.payload);self.assertEqual(len(raw),9360);self.assertEqual(digest(raw),GOLDEN_SHA);self.assertEqual(struct.unpack('<4sII',raw[:12]),(b'glTF',2,9360))
  pos=12;chunks=[]
  while pos<len(raw):
   size,kind=struct.unpack('<II',raw[pos:pos+8]);pos+=8;self.assertEqual(size%4,0);self.assertLessEqual(pos+size,len(raw));chunks.append((kind,size));pos+=size
  self.assertEqual(pos,9360);self.assertEqual(chunks[0][0],0x4e4f534a)
 def test_LF_CRLF_CR_and_mixed_literal_variants_decode_to_same_exact_bytes(self):
  lf=self.payload.replace(b'\r\n',b'\n').replace(b'\r',b'\n')
  variants=[lf,lf.replace(b'\n',b'\r\n'),lf.replace(b'\n',b'\r'),lf.replace(b'\n',b'\r\n',1)]
  for payload in variants:self.assertEqual((len(decode(payload)),digest(decode(payload))),(9360,GOLDEN_SHA))
 def test_old_LF_only_stripping_leaves_CR_in_CRLF_and_CR_literals(self):
  lf=self.payload.replace(b'\r\n',b'\n')
  self.assertEqual(digest(base64.b64decode(lf.replace(b'\n',b''),validate=True)),GOLDEN_SHA)
  for payload in (lf.replace(b'\n',b'\r\n'),lf.replace(b'\n',b'\r')):
   remaining=payload.replace(b'\n',b'');self.assertIn(b'\r',remaining)
   with self.assertRaises(ValueError):base64.b64decode(remaining,validate=True)
 def test_malformed_chunk_golden_remains_the_independent9364_byte_identity(self):
  raw=bytearray(decode(self.payload));raw.extend(b'JUNK');struct.pack_into('<I',raw,8,len(raw));self.assertEqual(len(raw),9364);self.assertEqual(digest(raw),BAD_SHA)
 def test_source_golden_constants_and_79_plus17_wrapper_unchanged(self):
  self.assertIn(('const GLB_SHA = "'+GOLDEN_SHA+'"').encode(),self.original)
  self.assertIn(('const BAD_CHUNKS_SHA = "'+BAD_SHA+'"').encode(),self.original)
  proof=json.loads((HERE/'SOURCE_PROOF.json').read_bytes())
  for name,expected in proof['unchanged_sources'].items():self.assertEqual(digest((HERE/('original-'+Path(name).name)).read_bytes()),expected)
  wrapper=(HERE/'original-verify_source_bone_bindings.py').read_bytes();self.assertIn(b"'SOURCE_BONE_BINDINGS ', 79",wrapper);self.assertIn(b"'SOURCE_NATIVE_HELPER_CHOICE ', 17",wrapper)
 def test_no_broad_whitespace_or_payload_repair_is_introduced(self):
  self.assertNotIn(b'.strip_edges()',NEW);self.assertEqual(literal(self.proposed),literal(self.original))
  with self.assertRaises(ValueError):decode(self.payload+b' ')
 def test_changed_base64_character_does_not_match_golden(self):
  raw=self.payload.replace(b'\r',b'').replace(b'\n',b'');changed=(b'A' if raw[:1]!=b'A' else b'B')+raw[1:];self.assertNotEqual(digest(decode(changed)),GOLDEN_SHA)
if __name__=='__main__':unittest.main()
