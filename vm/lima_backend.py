"""Portable full-VM backend. State stays private to this checkout."""
import datetime,json,os,pathlib,platform,shlex,shutil,subprocess,sys,time
from bootstrap import ROOT,PACKAGES,NETWORK_PACKAGES,keypair,payload,image
STATE=pathlib.Path(os.environ.get('LAB_LIMA_STATE',ROOT/'.lab/lima')).resolve()
KEY=ROOT/'.lab/id_ed25519'
BASE_PORT=int(os.environ.get('LAB_LIMA_BASE_PORT','2220'))
def run(args,**kwargs):return subprocess.run([str(x) for x in args],check=True,**kwargs)
def lima(*args,**kwargs):
 return run(['limactl','--tty=false',*args],env={**os.environ,'LIMA_HOME':str(STATE)},**kwargs)
def config():
 path=STATE/'labs.json'
 return json.loads(path.read_text()) if path.exists() else {}
def save(entries):
 STATE.mkdir(parents=True,exist_ok=True)
 path=STATE/'labs.json';temporary=path.with_suffix('.tmp');temporary.write_text(json.dumps(entries,indent=2)+'\n');temporary.replace(path)
def status(name):
 result=lima('list','--json',capture_output=True,text=True)
 entries=[json.loads(line) for line in result.stdout.splitlines() if line.strip()]
 return next((entry['status'] for entry in entries if entry['name']==name),'Missing')
def ssh_args(entry):
 return ['ssh','-o','BatchMode=yes','-o','ConnectTimeout=5','-o','StrictHostKeyChecking=accept-new','-o',f'UserKnownHostsFile={STATE}/known_hosts','-o','IdentitiesOnly=yes','-i',str(KEY),'-p',str(entry['port']),'trainee@127.0.0.1']
def remote(entry,command,**kwargs):return run(ssh_args(entry)+[command],**kwargs)
def wait(entry):
 deadline=time.monotonic()+240
 while time.monotonic()<deadline:
  result=subprocess.run(ssh_args(entry)+['true'],capture_output=True)
  if result.returncode==0:return
  if b'REMOTE HOST IDENTIFICATION HAS CHANGED' in result.stderr:
   raise RuntimeError('SSH host identity changed unexpectedly. Inspect the VM before updating its known-host entry.')
  time.sleep(2)
 raise RuntimeError('VM SSH did not become ready; inspect limactl logs in '+str(STATE))
def start(entry):
 if not entry.get('ready'):raise RuntimeError('Setup is incomplete. Rerun ./setup for this lab.')
 lima('start',entry['name']);wait(entry)
def stop(entry):
 if status(entry['name'])=='Running':lima('stop',entry['name'])
def reboot(entry):
 old=remote(entry,'cat /proc/sys/kernel/random/boot_id',capture_output=True,text=True).stdout
 lima('stop',entry['name']);lima('start',entry['name']);wait(entry)
 new=remote(entry,'cat /proc/sys/kernel/random/boot_id',capture_output=True,text=True).stdout
 if old==new:raise RuntimeError('Guest boot identity did not change.')
 remote(entry,'systemctl is-system-running --wait',capture_output=True)
def reset(entry):
 if not entry.get('ready'):raise RuntimeError('No fresh baseline; finish setup first.')
 stop(entry)
 tag='before-reset-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
 lima('snapshot','create',entry['name'],'--tag',tag)
 lima('snapshot','apply',entry['name'],'--tag','fresh')
 start(entry);print('Fresh exercise restored; previous state retained as snapshot '+tag)
def template(n,arch,disk,digest,port):
 return {'vmType':'qemu','plain':True,'arch':arch,'images':[{'location':str(disk),'arch':arch,'digest':'sha512:'+digest}],
 'cpus':1,'memory':'1GiB','disk':'10GiB','mounts':[],
 'user':{'name':'trainee','uid':1000,'home':'/home/trainee','shell':'/bin/bash'},
 'ssh':{'localPort':port,'loadDotSSHPubKeys':False,'forwardAgent':False},
 'containerd':{'system':False,'user':False},'propagateProxyEnv':False,
 'portForwards':[{'guestIP':'0.0.0.0','proto':'any','ignore':True}]}
def setup(selected):
 for binary in ('limactl','qemu-img','ssh','ssh-keygen'):
  if not shutil.which(binary):raise RuntimeError(f'Missing {binary}. On macOS run: brew install lima qemu python')
 arch={'arm64':'aarch64','aarch64':'aarch64','x86_64':'x86_64'}.get(platform.machine())
 if not arch:raise RuntimeError('Supported hosts: Apple Silicon/ARM64 and Intel/AMD x86_64.')
 keypair();STATE.mkdir(parents=True,exist_ok=True,mode=0o700)
 entries=config()
 pending=[n for n in selected if not entries.get(str(n),{}).get('ready')]
 if not pending:print('Selected labs already installed; setup preserved their state.');return
 disk,digest=image(arch)
 archive=payload(STATE/'bootstrap.tar.gz')
 for n in pending:
  entry=entries.setdefault(str(n),{'name':f'lab{n}','port':BASE_PORT+n,'ready':False})
  save(entries)
  if status(entry['name'])=='Missing':
   if (STATE/'known_hosts').exists():run(['ssh-keygen','-R',f'[127.0.0.1]:{entry["port"]}','-f',str(STATE/'known_hosts')],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
   path=STATE/f'lab{n}.yaml';path.write_text(json.dumps(template(n,arch,disk,digest,entry['port']),indent=2)+'\n')
   lima('start','--name',entry['name'],path)
  else:lima('start',entry['name'])
  # Lima's own SSH key bootstraps our dedicated learner key; no host mounts are needed.
  public=KEY.with_suffix('.pub').read_text().strip()
  lima('shell','--workdir=/home/trainee',entry['name'],'sh','-c','printf "%s\\n" '+shlex.quote(public)+' >> ~/.ssh/authorized_keys')
  wait(entry)
  remote(entry,"printf 'ssh_deletekeys: false\\n' | sudo tee /etc/cloud/cloud.cfg.d/99-lab-ssh.cfg >/dev/null")
  installed=subprocess.run(ssh_args(entry)+[f'test "$(cat /var/lib/devops-lab/ready 2>/dev/null)" = {n}'],capture_output=True)
  if installed.returncode!=0:
   packages=PACKAGES+(NETWORK_PACKAGES if n>=6 else [])
   command='sudo env DEBIAN_FRONTEND=noninteractive apt-get update -qq && sudo env DEBIAN_FRONTEND=noninteractive apt-get install -y '+shlex.join(packages)
   remote(entry,command,stdout=subprocess.DEVNULL)
   remote(entry,'sudo systemctl disable --now nginx cron; sudo usermod -aG systemd-journal trainee; sudo hostnamectl set-hostname incident-'+str(n))
   with archive.open('rb') as stream:remote(entry,'sudo tar -xzf - -C /tmp',stdin=stream)
   remote(entry,f'sudo bash /tmp/lab/guest-init.sh {n}')
  wait(entry);remote(entry,'systemctl is-system-running --wait && test -r ~/problem.md')
  stop(entry)
  # Completion is recorded only after the clean disk snapshot succeeds.
  lima('snapshot','create',entry['name'],'--tag','fresh')
  entry['ready']=True;save(entries);start(entry)
  print(f'Lab {n} installed; SSH localhost:{entry["port"]}',flush=True)
def main(args):
 entries=config()
 if args.command=='hint':
  if not args.incident or not args.level:raise RuntimeError('Usage: ./labctl hint N LEVEL')
  print((ROOT/f'instructor/hints/{args.incident}-{args.level}.md').read_text());return
 if not entries:raise RuntimeError('No labs installed. Run ./setup 1 first.')
 selected=[str(args.incident)] if args.incident else list(entries)
 if args.command=='test':os.execv(sys.executable,[sys.executable,str(ROOT/'vm/test_lima.py')]+([str(args.incident)] if args.incident else []))
 for n in selected:
  if n not in entries:raise RuntimeError(f'Lab {n} is not installed. Run ./setup {n}.')
  entry=entries[n]
  if args.command=='status':print(f'lab{n}: {status(entry["name"])}; SSH localhost:{entry["port"]}')
  elif args.command=='start':start(entry)
  elif args.command=='stop':stop(entry)
  elif args.command=='restart':reboot(entry)
  elif args.command=='reset':reset(entry)
  elif args.command=='ssh':
   if status(entry['name'])!='Running':raise RuntimeError(f'Run ./labctl start {n} first.')
   os.execvp('ssh',ssh_args(entry))
  elif args.command in ('verify','durable'):
   remote(entry,'verify')
   if args.command=='durable':reboot(entry);remote(entry,'verify')
  elif args.command=='console':raise RuntimeError('Use SSH for login; boot logs are under '+str(STATE/entry['name']))
