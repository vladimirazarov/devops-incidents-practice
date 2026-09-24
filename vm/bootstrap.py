"""Shared fresh-install assets; contains instructor provisioning references."""
import hashlib, pathlib, subprocess, tarfile, urllib.request
ROOT=pathlib.Path(__file__).resolve().parents[1]
PACKAGES=['qemu-guest-agent','openssh-server','sudo','nginx-light','python3','curl','iproute2','iputils-ping','dnsutils','netcat-openbsd','procps','lsof','strace','less','vim-tiny','nano','cron','ca-certificates','logrotate','libpam-systemd','dbus-user-session']
NETWORK_PACKAGES=['dnsmasq','nftables','tcpdump','traceroute','mtr-tiny','openssl','conntrack','ethtool']
def keypair():
 directory=ROOT/'.lab';directory.mkdir(exist_ok=True,mode=0o700)
 key=directory/'id_ed25519'
 if not key.exists():subprocess.run(['ssh-keygen','-q','-t','ed25519','-N','','-C','devops-practice','-f',str(key)],check=True)
 if not key.with_suffix('.pub').exists():
  key.with_suffix('.pub').write_text(subprocess.check_output(['ssh-keygen','-y','-f',str(key)],text=True))
 return key

def payload(path):
 path.parent.mkdir(parents=True,exist_ok=True)
 with tarfile.open(path,'w:gz') as archive:
  for name in ('seed.py','systemd_common.py','content.json','service.py','verify.py','export-report','publish-report'):
   archive.add(ROOT/'lab'/name,arcname='lab/'+name)
  archive.add(ROOT/'vm/guest-init.sh',arcname='lab/guest-init.sh')
  archive.add(ROOT/'lab/network',arcname='lab/network',filter=lambda item:None if '__pycache__' in item.name else item)
 return path

def image(arch,directory=None):
 debarch={'x86_64':'amd64','aarch64':'arm64'}[arch]
 directory=directory or ROOT/'.lab/images';directory.mkdir(parents=True,exist_ok=True)
 name=f'debian-12-genericcloud-{debarch}.qcow2';target=directory/name
 receipt=target.with_suffix('.sha512')
 if target.exists() and receipt.exists():
  expected=receipt.read_text().strip()
 elif target.exists() and (directory/'verified.txt').exists() and name in (directory/'verified.txt').read_text():
  expected=next(line.split()[1] for line in (directory/'verified.txt').read_text().splitlines() if line.startswith('SHA512 '))
 else:
  base='https://cloud.debian.org/images/cloud/bookworm/latest/'
  with urllib.request.urlopen(base+'SHA512SUMS',timeout=60) as response:checks=response.read().decode()
  expected=next(line.split()[0] for line in checks.splitlines() if line.split()[-1].lstrip('*').removeprefix('./')==name)
  if target.exists():
   with target.open('rb') as source:actual=hashlib.file_digest(source,'sha512').hexdigest()
   if actual!=expected:raise RuntimeError('Existing base image differs from current Debian release. Refusing to replace a possible VM backing file.')
   receipt.write_text(expected+'\n');return target.resolve(),expected
  print(f'Downloading Debian 12 ({arch})...',flush=True)
  temporary=target.with_suffix('.download')
  urllib.request.urlretrieve(base+name,temporary)
  with temporary.open('rb') as source:actual=hashlib.file_digest(source,'sha512').hexdigest()
  if actual!=expected:
   temporary.unlink();raise RuntimeError('Debian image checksum mismatch; retry setup.')
  temporary.replace(target);receipt.write_text(expected+'\n')
 with target.open('rb') as source:actual=hashlib.file_digest(source,'sha512').hexdigest()
 if actual!=expected:raise RuntimeError('Cached Debian image checksum mismatch.')
 if not receipt.exists():receipt.write_text(expected+'\n')
 return target.resolve(),expected
