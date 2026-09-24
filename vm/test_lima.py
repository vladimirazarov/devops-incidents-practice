#!/usr/bin/env python3
"""Instructor integration checks in a separate, disposable Lima home."""
import argparse,json,os,pathlib,shlex,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('incidents',nargs='*',type=int,choices=range(1,9))
selected=parser.parse_args().incidents or list(range(1,9))
os.environ['LAB_LIMA_STATE']=str(ROOT/'.lab'/('lima-tests-'+'-'.join(map(str,selected))))
os.environ['LAB_LIMA_BASE_PORT']='4220'
import lima_backend as backend
fixes=json.loads((ROOT/'instructor/fixes.json').read_text())
for n in selected:
 try:
  backend.setup([n]);entry=backend.config()[str(n)]
  def remote(command,success=True):
   result=subprocess.run(backend.ssh_args(entry)+[command],capture_output=True,text=True,timeout=110)
   if (result.returncode==0)!=success:raise RuntimeError(f'Lab {n} failed: {command}\n{result.stdout}\n{result.stderr}')
  remote('test "$(cat /proc/1/comm)" = systemd && systemctl is-system-running --wait')
  remote('test -r ~/problem.md && test ! -e ~/skills.md && test ! -e ~/incident-notes.md')
  remote('verify',False)
  remote('sudo sh -c '+shlex.quote(fixes[str(n)]));remote('verify')
  backend.reboot(entry);remote('verify')
  backend.reset(entry);remote('verify',False)
  print(f'PASS lab {n}: fresh install, repair, reboot and reset',flush=True)
 finally:
  entries=backend.config()
  if str(n) in entries:
   entry=entries[str(n)]
   if backend.status(entry['name'])!='Missing':
    backend.stop(entry);backend.lima('delete','--force',entry['name'])
   entries.pop(str(n));backend.save(entries)
