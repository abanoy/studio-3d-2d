"""Real OS-lock reservations, crash identity, fail-closed registry and path safety."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase,mock
import base64,json,os,subprocess,sys
from concurrent.futures import ThreadPoolExecutor
from tools import recovery_quota as Q
from tools.recovery_processes import details

ROOT=Path(__file__).resolve().parents[1]
def owner(pid=None):
 pid=pid or os.getpid();d=details([pid]);field='linux_start' if sys.platform=='linux' else 'created_100ns'
 return {'pid':pid,field:d[field][str(pid)]}

class QuotaTests(TestCase):
 def setUp(self):self.tmp=TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)/'recovery';self.me=owner()
 def rows(self):return json.loads((self.root/'.quota.json').read_bytes())['reservations']
 def test_reserve_release_preserves_data(self):
  self.root.mkdir();source=self.root/'previous.bin';source.write_bytes(b'preserve')
  Q.operation(self.root,'reserve','one',self.me,1024);self.assertEqual(self.rows()['one']['bytes'],1024)
  Q.operation(self.root,'release','one',self.me);self.assertEqual(self.rows(),{});self.assertEqual(source.read_bytes(),b'preserve')
 def test_parallel_cli_admits_only_one_large_checkpoint(self):
  def attempt(token):
   p=subprocess.run([sys.executable,str(ROOT/'tools/recovery_quota.py'),str(self.root),'reserve',token,base64.b64encode(json.dumps(self.me).encode()).decode(),str(270*1024*1024)],capture_output=True,text=True,timeout=10)
   self.assertEqual(p.returncode,0,p.stderr);return json.loads(p.stdout)
  with ThreadPoolExecutor(2) as pool:results=list(pool.map(attempt,['first','second']))
  self.assertEqual(sum(r['ok'] for r in results),1);self.assertEqual(len(self.rows()),1)
  self.assertLessEqual(sum(r['bytes'] for r in self.rows().values()),Q.MAX_BYTES)
 def test_crashed_process_reservation_is_reclaimed_without_deleting_data(self):
  code='import sys,json,os;from tools.recovery_quota import operation;from tools.recovery_processes import details;d=details([os.getpid()]);f="linux_start" if sys.platform=="linux" else "created_100ns";o={"pid":os.getpid(),f:d[f][str(os.getpid())]};operation(sys.argv[1],"reserve","crashed",o,270*1024*1024);print("ready",flush=True);sys.stdin.readline()'
  child=subprocess.Popen([sys.executable,'-c',code,str(self.root)],cwd=ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
  try:
   self.assertEqual(child.stdout.readline().strip(),'ready');self.assertIn('crashed',self.rows());child.kill();child.wait(timeout=5)
   Q.operation(self.root,'reserve','new',self.me,270*1024*1024);self.assertEqual(set(self.rows()),{'new'})
  finally:
   if child.poll() is None:child.kill();child.wait(timeout=5)
   child.communicate(timeout=5)
 def test_unknown_owner_is_retained(self):
  Q.operation(self.root,'reserve','old',self.me,270*1024*1024)
  dead=dict(self.me);dead['pid']=2147483646
  p=self.root/'.quota.json';data=json.loads(p.read_bytes());data['reservations']['old']['owner']=dead;p.write_text(json.dumps(data))
  d=details([os.getpid()]);d['owners'][str(dead['pid'])]='unknown'
  with mock.patch.object(Q,'details',return_value=d):
   with self.assertRaisesRegex(ValueError,'budget'):Q.operation(self.root,'reserve','new',self.me,270*1024*1024)
  self.assertIn('old',self.rows())
 def test_occupied_bytes_reduce_admission(self):
  self.root.mkdir()
  with (self.root/'existing.bin').open('wb') as stream:stream.truncate(503*1024*1024)
  Q.operation(self.root,'reserve','one',self.me,6*1024*1024)
  with self.assertRaisesRegex(ValueError,'budget'):Q.operation(self.root,'reserve','two',self.me,6*1024*1024)
  self.assertEqual((self.root/'existing.bin').stat().st_size,503*1024*1024)
 def test_corrupt_registry_is_preserved(self):
  self.root.mkdir();p=self.root/'.quota.json';p.write_bytes(b'{bad')
  with self.assertRaises(ValueError):Q.operation(self.root,'reserve','one',self.me,1024)
  self.assertEqual(p.read_bytes(),b'{bad')
 def test_linked_registry_and_lock_refuse(self):
  self.root.mkdir();outside=Path(self.tmp.name)/'outside';outside.write_bytes(b'original')
  for name in ['.quota.json','.quota.lock']:
   link=self.root/name
   if link.exists():link.unlink()
   try:link.symlink_to(outside)
   except OSError:self.skipTest('Symbolic links unavailable')
   with self.assertRaises(ValueError):Q.operation(self.root,'reserve','one',self.me,1024)
   link.unlink();self.assertEqual(outside.read_bytes(),b'original')
 def test_wrong_incarnation_cannot_release(self):
  Q.operation(self.root,'reserve','one',self.me,1024);other=dict(self.me);field=next(k for k in other if k!='pid');other[field]=other[field][:-1]+('1' if other[field][-1]!='1' else '2')
  with self.assertRaisesRegex(ValueError,'verify'):Q.operation(self.root,'release','one',other)
  self.assertIn('one',self.rows())
