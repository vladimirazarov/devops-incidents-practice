#!/usr/bin/env python3
"""Render all image seed files in a temporary tree without host administration."""
import configparser, json, os, pathlib, subprocess, sys, tempfile, unittest
from unittest.mock import patch
ROOT=pathlib.Path(__file__).resolve().parents[1]
SEED=compile((ROOT/'lab/seed.py').read_text(),'seed.py','exec')
CONTENT=(ROOT/'lab/content.json').read_text()
sys.path.insert(0,str(ROOT/'lab'))
class ScaffoldTests(unittest.TestCase):
 def test_all_five_seed_layouts_and_reference_edits(self):
  for n in range(1,6):
   with self.subTest(incident=n), tempfile.TemporaryDirectory() as tmp:
    base=pathlib.Path(tmp)
    def mapped(p):return base/str(p).lstrip('/')
    mapped('/tmp/lab').mkdir(parents=True);mapped('/tmp/lab/content.json').write_text(CONTENT)
    def chmod(p,mode):os_chmod(mapped(p),mode)
    def administration(command,**kwargs):
     # Validate shell syntax, but do not administer the host.
     return real_run(['/bin/sh','-n','-c',command],check=True)
    real_run=subprocess.run;os_chmod=os.chmod
    with patch('pathlib.Path',side_effect=mapped),patch('os.chmod',side_effect=chmod),patch('subprocess.run',side_effect=administration),patch.object(sys,'argv',['seed.py',str(n)]):
     sys.modules.pop('systemd_common',None)
     exec(SEED,{'__name__':'__main__'})
    self.assertIn('Recovery criteria',mapped('/home/trainee/problem.md').read_text())
    self.assertEqual(sorted(p.name for p in mapped('/home/trainee').iterdir()),['problem.md'])
    for conf in mapped('/etc/systemd/system').glob('*.service'):
     parser=configparser.ConfigParser(strict=False);parser.read(conf)
    # Run only reference sed edits, safely redirected to this generated tree.
    fix=json.loads((ROOT/'instructor/fixes.json').read_text())[str(n)]
    if fix.startswith('sed '):
     import shlex
     args=shlex.split(fix.split(' && ')[0]);args[-1]=str(mapped(args[-1]))
     # A backup suffix is accepted by both GNU sed and macOS BSD sed.
     args=["-i.bak" if arg=="-i" else arg for arg in args]
     subprocess.run(args,check=True)
    if n==1:self.assertIn('127.0.0.1:9000',mapped('/etc/nginx/nginx.conf').read_text())
    if n==3:self.assertIn('no_proxy=localhost,127.0.0.1,inventory.internal',mapped('/etc/systemd/system/gateway.service').read_text())
    if n==4:self.assertIn('OPEN_FILES=256',mapped('/etc/default/processor').read_text())
    if n==5:self.assertIn('reporter /usr/local/bin/export-report',mapped('/etc/cron.d/report-export').read_text())
if __name__=='__main__':unittest.main(verbosity=2)
