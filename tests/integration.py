#!/usr/bin/env python3
"""Destructive only to the dedicated test project. Instructor reference fixes are spoilers."""
import argparse, concurrent.futures, json, pathlib, subprocess, time
parser=argparse.ArgumentParser()
parser.add_argument("--incident",type=int,choices=range(1,6))
parser.add_argument("--project",default="devops-practice-tests")
args=parser.parse_args()
if not args.project.startswith("devops-practice-tests"):parser.error("Test project must start with devops-practice-tests")
selected=[args.incident] if args.incident else list(range(1,6))
ROOT=pathlib.Path(__file__).resolve().parents[1]
STATE=ROOT/'.lab';STATE.mkdir(exist_ok=True)
PROJECT=args.project
def run(args,**kwargs):
 try:return subprocess.run(args,cwd=ROOT,text=True,check=True,**kwargs)
 except subprocess.CalledProcessError as e:
  print(e.stdout or '',e.stderr or '',flush=True)
  raise
run(['docker','info'],stdout=subprocess.DEVNULL)
key=STATE/'test_ed25519'
if not key.exists():run(['ssh-keygen','-q','-t','ed25519','-N','','-f',str(key)])
config=json.loads(run(['docker','compose','config','--format','json'],capture_output=True).stdout)
config.pop('name',None)
config['services']={k:v for k,v in config['services'].items() if k in {f'lab{n}' for n in selected}}
config['networks']={k:v for k,v in config['networks'].items() if k in {f'incident{n}' for n in selected}}
for net in config['networks'].values():net.pop('name',None)
for svc in config['services'].values():
 svc['ports']=[{'target':22,'published':'0','host_ip':'127.0.0.1','protocol':'tcp'}]
 for volume in svc['volumes']:
  if volume['target']=='/etc/lab/authorized_key.pub':volume['source']=str(key)+'.pub'
configpath=STATE/(PROJECT+'-compose.json');configpath.write_text(json.dumps(config))
base=['docker','compose','-p',PROJECT,'-f',str(configpath)]
def dc(*args,**kwargs):return run(base+list(args),**kwargs)
def execute(n,command,success=True):
 result=subprocess.run(base+['exec','-T',f'lab{n}','sh','-c',command],cwd=ROOT,text=True,capture_output=True,timeout=100)
 if (result.returncode==0)!=success:raise AssertionError(f'Incident {n}, {command}: unexpected exit {result.returncode}\n{result.stdout}\n{result.stderr}')
 return result.stdout
fixes=json.loads((ROOT/'instructor/fixes.json').read_text())
def check_incident(n):
 name=f'lab{n}'
 port=dc('port',name,'22',capture_output=True).stdout.strip().rsplit(':',1)[1]
 # Strict checking against a fresh, per-test known_hosts avoids stale recreated keys.
 known=STATE/f'test-known-hosts-{n}'
 known.write_text('')
 run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=accept-new','-o',f'UserKnownHostsFile={known}','-o','IdentitiesOnly=yes','-i',str(key),'-p',port,'trainee@127.0.0.1','test -r ~/problem.md && test ! -e ~/skills.md && test ! -e ~/incident-notes.md && sudo -n true && systemctl --user is-system-running --wait'],capture_output=True,timeout=15)
 execute(n,'test "$(cat /proc/1/comm)" = systemd && systemctl is-system-running --wait && systemctl is-active ssh.service && journalctl --no-pager -u ssh.service -n 1')
 execute(n,'verify',False)
 print(f'Incident {n}: initial failure and SSH confirmed',flush=True)
 if n==2:
  execute(n,'chmod 640 /srv/reports/current.txt')
  execute(n,'verify',False)
  print('Incident 2: temporary recovery correctly rejected',flush=True)
 execute(n,fixes[str(n)])
 execute(n,'verify')
 dc('restart',name,capture_output=True);time.sleep(4)
 execute(n,'verify')
 if n==1:
  boot=execute(n,'cat /proc/sys/kernel/random/boot_id').strip()
  # The entrypoint supplies a virtual boot ID; wait for an actual new boot.
  subprocess.run(base+['exec','-T',name,'systemctl','reboot'],capture_output=True)
  deadline=time.monotonic()+45
  while time.monotonic()<deadline:
   time.sleep(1)
   result=subprocess.run(base+['exec','-T',name,'sh','-c','systemctl is-system-running --wait >/dev/null && cat /proc/sys/kernel/random/boot_id'],capture_output=True,text=True,timeout=10)
   if result.returncode==0 and result.stdout.strip()!=boot:break
  else:raise AssertionError('systemctl reboot did not complete a new boot')
  execute(n,'journalctl --list-boots --no-pager | grep -q -- "-1"')
  execute(n,'verify')
  print('Incident 1: systemctl reboot and retained journal confirmed',flush=True)
 print(f'Incident {n}: fix and restart durability confirmed',flush=True)
 dc('up','-d','--force-recreate','--wait',name,capture_output=True)
 execute(n,'verify',False)
 print(f'Incident {n}: reset restores the failure',flush=True)
try:
 dc('up','-d','--build','--wait','--wait-timeout','90')
 with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
  for future in [pool.submit(check_incident,n) for n in selected]:future.result()
 print(f'PASS: incidents {selected}, SSH, fixes, restart durability, and resets.')
finally:
 dc('down','--remove-orphans',capture_output=True)
