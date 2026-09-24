"""Provision fresh exercise baselines. Does not modify existing learner containers."""
import argparse, concurrent.futures, json, pathlib, tarfile
parser=argparse.ArgumentParser()
parser.add_argument("incidents",nargs="*",type=int,choices=range(1,9))
selected=parser.parse_args().incidents or list(range(1,9))
from runtime import *
from bootstrap import payload as build_payload, PACKAGES, NETWORK_PACKAGES
payload=build_payload(STATE/'bootstrap.tar.gz')
config={}
if (STATE/'config.json').exists():config=read_config()
for n in selected:config.setdefault(str(n),{'name':f'devops-lab{n}','port':2220+n,'directory':str(STATE/f'lab{n}')})
(STATE/'config.json').write_text(json.dumps(config,indent=2)+'\n')
def provision(n):
 entry=config[str(n)];directory=pathlib.Path(entry['directory']);directory.mkdir(parents=True,exist_ok=True)
 name=entry['name'];port=entry['port'];live=directory/'live.qcow2';baseline=directory/'baseline.qcow2'
 if baseline.exists():
  print(f'Lab {n}: baseline already exists',flush=True);return
 if domstate(name)=='running':shutdown(name)
 packages=PACKAGES+(NETWORK_PACKAGES if n>=6 else [])
 seed=cloud_seed(directory/'seed',f'devops-lab{n}-fresh-v3',f'incident-{n}',packages)
 if not live.exists():
  overlay(live,STATE/'base/debian-12-genericcloud-amd64.qcow2')
  run(['qemu-img','resize',live,'10G'],capture_output=True)
 define(name,live,seed,port)
 if domstate(name)!='running':virsh('start',name,capture_output=True)
 wait_ssh(port)
 ssh(port,'sudo cloud-init status --wait',capture_output=True,timeout=900)
 with payload.open('rb') as file:ssh(port,'sudo tar -xzf - -C /tmp',stdin=file,capture_output=True)
 ssh(port,f'sudo bash /tmp/lab/guest-init.sh {n}',capture_output=True,timeout=90)
 wait_ssh(port)
 ssh(port,'test "$(systemd-detect-virt)" = kvm && systemctl is-system-running --wait && test -r ~/problem.md',capture_output=True)
 shutdown(name)
 live.rename(baseline);baseline.chmod(0o444)
 overlay(live,baseline)
 virsh('start',name,capture_output=True);wait_ssh(port)
 print(f'Lab {n}: fresh VM and independent reset baseline ready',flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
 for result in [pool.submit(provision,n) for n in selected]:result.result()
