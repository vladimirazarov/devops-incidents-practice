"""Host-only portability checks: no VM or administrator access required."""
import hashlib,json,pathlib,sys,tempfile,unittest
from unittest.mock import patch
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'vm'))
import bootstrap,lima_backend
class Portability(unittest.TestCase):
 def test_native_configs_do_not_share_host_files_or_forward_services(self):
  for arch in ('x86_64','aarch64'):
   cfg=lima_backend.template(6,arch,pathlib.Path('/tmp/base.qcow2'),'a'*128,2226)
   self.assertEqual(cfg['arch'],arch)
   self.assertTrue(cfg['plain'])
   self.assertEqual(cfg['images'][0]['arch'],arch)
   self.assertEqual(cfg['mounts'],[])
   self.assertFalse(cfg['containerd']['user'])
   self.assertFalse(cfg['ssh']['forwardAgent'])
   self.assertTrue(cfg['portForwards'][0]['ignore'])
   self.assertEqual(cfg['user']['home'],'/home/trainee')
   self.assertEqual(cfg['ssh']['localPort'],2226)
 def test_existing_backing_image_is_verified_without_download_or_replacement(self):
  with tempfile.TemporaryDirectory() as tmp:
   directory=pathlib.Path(tmp);disk=directory/'debian-12-genericcloud-amd64.qcow2'
   disk.write_bytes(b'existing backing image');expected=hashlib.sha512(disk.read_bytes()).hexdigest()
   (directory/'verified.txt').write_text(disk.name+'\nSHA512 '+expected+'\n')
   with patch('urllib.request.urlopen',side_effect=AssertionError('Network must not be used')):
    result,digest=bootstrap.image('x86_64',directory)
   self.assertEqual(result,disk.resolve());self.assertEqual(digest,expected)
   self.assertEqual(disk.read_bytes(),b'existing backing image')
 def test_corrupted_cache_is_rejected(self):
  with tempfile.TemporaryDirectory() as tmp:
   directory=pathlib.Path(tmp);disk=directory/'debian-12-genericcloud-arm64.qcow2'
   disk.write_bytes(b'corrupt');disk.with_suffix('.sha512').write_text('0'*128)
   with self.assertRaisesRegex(RuntimeError,'checksum mismatch'):bootstrap.image('aarch64',directory)
 def test_ready_setup_is_noop(self):
  with tempfile.TemporaryDirectory() as tmp,patch.object(lima_backend,'STATE',pathlib.Path(tmp)),patch.object(lima_backend,'keypair'),patch.object(lima_backend.shutil,'which',return_value='/bin/tool'),patch.object(lima_backend,'image',side_effect=AssertionError('Must not download')):
   original={'1':{'name':'lab1','port':2221,'ready':True}}
   lima_backend.save(original);lima_backend.setup([1]);self.assertEqual(lima_backend.config(),original)
 def test_reset_archives_before_restoring(self):
  calls=[]
  with patch.object(lima_backend,'stop',side_effect=lambda e:calls.append('stop')),patch.object(lima_backend,'start',side_effect=lambda e:calls.append('start')),patch.object(lima_backend,'lima',side_effect=lambda *a:calls.append(a)):
   lima_backend.reset({'name':'lab1','ready':True})
  self.assertEqual(calls[0],'stop');self.assertEqual(calls[1][:2],('snapshot','create'))
  self.assertEqual(calls[2],('snapshot','apply','lab1','--tag','fresh'));self.assertEqual(calls[3],'start')
if __name__=='__main__':unittest.main()
