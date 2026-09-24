"""Instructor-only functional tests in disposable VM disk overlays."""
import argparse,concurrent.futures,json,pathlib,time
parser=argparse.ArgumentParser()
parser.add_argument("incidents",nargs="*",type=int,choices=range(1,9))
selected=parser.parse_args().incidents or list(range(1,9))
from runtime import *
config=read_config();fixes=json.loads((ROOT/'instructor/fixes.json').read_text())
STATE.joinpath('tests').mkdir(exist_ok=True)
def test(n):
 directory=STATE/'tests'/f'lab{n}';directory.mkdir(exist_ok=True)
 disk=directory/'test.qcow2';name=f'devops-test{n}';port=3320+n
 if disk.exists():raise RuntimeError(f'Previous test disk remains: {disk}')
 baseline=pathlib.Path(config[str(n)]['directory'])/'baseline.qcow2'
 seed=pathlib.Path(config[str(n)]['directory'])/'seed/seed.iso'
 overlay(disk,baseline);define(name,disk,seed,port)
 def remote(command,success=True,timeout=100):
  result=ssh(port,command,check=False,capture_output=True,timeout=timeout)
  if (result.returncode==0)!=success:raise RuntimeError(f'Lab {n} test failed: {command}\n{result.stdout}\n{result.stderr}')
  return result.stdout
 try:
  virsh('start',name,capture_output=True);wait_ssh(port)
  remote('test "$(systemd-detect-virt)" = kvm && systemctl is-system-running --wait && systemctl --user is-system-running --wait')
  remote('test -r ~/problem.md && test ! -e ~/skills.md && test ! -e ~/incident-notes.md')
  if n<5:remote("sudo ss -ltpn 'sport = :8080' | grep -q 'users:('")
  if n in (6,7):remote('sudo ip netns exec backend curl -fsS http://127.0.0.1:8080/')
  if n==8:
   remote('curl -fsS http://127.0.0.1:8080/')
   remote('curl -kfsS --noproxy "*" https://checkout.lab.test:8443/')
  remote('verify',False)
  if n==2:
   remote('sudo chmod 640 /srv/reports/current.txt');remote('verify',False)
  remote('sudo sh -c '+shlex.quote(fixes[str(n)]))
  remote('verify')
  if n==6:
   remote('sudo ip netns exec client dig +short orders.svc.test | grep -qx 10.80.2.2')
   remote('sudo ip netns exec client dig +tcp +short catalog.svc.test | grep -qx 10.80.2.2')
  if n==7:
   remote('sudo nft delete table inet site');remote('verify',False)
   remote('sudo nft -f /etc/site-firewall.nft');remote('verify')
  reboot(name,port);remote('verify');remote("sudo journalctl --list-boots --no-pager | grep -q -- '-1'")
  shutdown(name);disk.unlink();overlay(disk,baseline)
  virsh('start',name,capture_output=True);wait_ssh(port);remote('verify',False)
  print(f'Lab {n}: VM diagnostics, failure, fix, reboot and reset passed',flush=True)
 finally:
  if domstate(name) not in ('undefined','shut off'):shutdown(name)
  if domstate(name)!='undefined':virsh('undefine',name,capture_output=True)
  # Only these disposable test overlays are removed; baselines and learner disks are retained.
  disk.unlink(missing_ok=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
 for result in [pool.submit(test,n) for n in selected]:result.result()
(STATE/('vm-tests-'+ '-'.join(map(str,selected)) +'-passed')).write_text('Selected VM exercises passed diagnostics, failure, fix, reboot and reset checks.\n')
print('PASS: selected VM exercises.',flush=True)
