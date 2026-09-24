#!/usr/bin/env python3
"""Host-side functional tests; Docker integration remains a separate requirement."""
import contextlib, http.server, json, os, pathlib, resource, socket, subprocess, tempfile, threading, time, unittest, urllib.error, urllib.request
ROOT=pathlib.Path(__file__).resolve().parents[1]
def free_port():
 with socket.socket() as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]
@contextlib.contextmanager
def service(mode='echo',limit=None,extra_env=None):
 port=free_port();env={**os.environ,'MODE':mode,'PORT':str(port),**(extra_env or {})}
 def limits():resource.setrlimit(resource.RLIMIT_NOFILE,(limit,limit))
 process=subprocess.Popen(['python3',str(ROOT/'lab/service.py')],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,preexec_fn=limits if limit else None)
 try:
  for _ in range(100):
   try:
    with socket.create_connection(('127.0.0.1',port),timeout=.1):break
   except OSError:
    if process.poll() is not None:raise RuntimeError('service exited before listening')
    time.sleep(.02)
  else:raise RuntimeError('service startup timed out')
  yield port
 finally:process.terminate();process.wait(timeout=5)
def request(port,query):
 with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(f'http://127.0.0.1:{port}/{query}',timeout=3) as r:return json.load(r)
class FunctionalTests(unittest.TestCase):
 def test_echo_reflects_distinct_requests(self):
  with service() as port:
   for token in ['alpha','beta%20two','new-value']:
    self.assertEqual(request(port,'?token='+token)['value'],urllib.parse.unquote(token))
 def test_low_limit_fails_large_batch_then_recovers_small_batch(self):
  with service('capacity',32) as port:
   self.assertEqual(request(port,'?batch=1&token=x')['value'],'x:1')
   with self.assertRaises(urllib.error.HTTPError) as error:request(port,'?batch=80')
   self.assertEqual(error.exception.code,503);error.exception.close()
   self.assertEqual(request(port,'?batch=2&token=y')['value'],'y:2')
 def test_sufficient_limit_supports_repeated_batches(self):
  with service('capacity',256) as port:
   for _ in range(10):self.assertEqual(request(port,'?batch=80&token=x')['value'],'x:80')
 def test_gateway_proxy_environment_and_bypass(self):
  with service() as backend, tempfile.TemporaryDirectory() as tmp:
   config=pathlib.Path(tmp)/'service.json'
   config.write_text(json.dumps({'inventory_url':f'http://127.0.0.1:{backend}'}))
   env={'SERVICE_CONFIG':str(config),'http_proxy':f'http://127.0.0.1:{free_port()}','no_proxy':''}
   with service('gateway',extra_env=env) as gateway:
    with self.assertRaises(urllib.error.HTTPError) as error:request(gateway,'?token=probe')
    self.assertEqual(error.exception.code,503);error.exception.close()
   env['no_proxy']='127.0.0.1'
   with service('gateway',extra_env=env) as gateway:
    self.assertEqual(request(gateway,'?token=fresh-result')['value'],'fresh-result')
 def test_export_computes_fresh_atomic_private_output(self):
  with tempfile.TemporaryDirectory() as tmp:
   d=pathlib.Path(tmp);src=d/'source.json';dest=d/'export.json'
   src.write_text('{"batch":"test-batch","amounts":[11,19,-2]}');dest.write_text('old')
   inode=dest.stat().st_ino
   script=(ROOT/'lab/export-report').read_text().replace('/srv/orders/current.json',str(src)).replace('/srv/exports/current.json',str(dest))
   subprocess.run(['/bin/sh'],input=script,text=True,check=True)
   result=json.loads(dest.read_text())
   self.assertEqual(result['total'],28);self.assertEqual(result['batch'],'test-batch')
   self.assertNotEqual(dest.stat().st_ino,inode);self.assertEqual(dest.stat().st_mode&7,0)
   self.assertLess(abs(time.time()-result['generated_at']),5)
 def test_export_preserves_previous_output_on_invalid_input(self):
  with tempfile.TemporaryDirectory() as tmp:
   d=pathlib.Path(tmp);src=d/'source.json';dest=d/'export.json';src.write_text('invalid');dest.write_text('previous')
   script=(ROOT/'lab/export-report').read_text().replace('/srv/orders/current.json',str(src)).replace('/srv/exports/current.json',str(dest))
   result=subprocess.run(['/bin/sh'],input=script,text=True,capture_output=True)
   self.assertNotEqual(result.returncode,0);self.assertEqual(dest.read_text(),'previous')
if __name__=='__main__':unittest.main(verbosity=2)
