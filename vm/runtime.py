"""Local KVM/libvirt session runtime. Guest disks and keys remain in .lab/."""
import hashlib, json, os, pathlib, shlex, subprocess, time, uuid, xml.etree.ElementTree as ET
ROOT=pathlib.Path(__file__).resolve().parents[1]
STATE=ROOT/'.lab/vm'
URI='qemu:///session'
KEY=ROOT/'.lab/id_ed25519'
def run(args,check=True,**kwargs):
 return subprocess.run([str(x) for x in args],check=check,text=True,**kwargs)
def virsh(*args,**kwargs):return run(['virsh','-c',URI,*args],**kwargs)
def domstate(name):
 result=virsh('domstate',name,check=False,capture_output=True)
 return result.stdout.strip() if result.returncode==0 else 'undefined'
def ssh(port,command,check=True,**kwargs):
 return run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=4','-o','StrictHostKeyChecking=accept-new','-o',f'UserKnownHostsFile={STATE}/known_hosts','-o','IdentitiesOnly=yes','-i',KEY,'-p',str(port),'trainee@127.0.0.1',command],check=check,**kwargs)
def wait_ssh(port,timeout=240):
 deadline=time.monotonic()+timeout
 while time.monotonic()<deadline:
  if ssh(port,'true',check=False,capture_output=True).returncode==0:return
  time.sleep(2)
 raise RuntimeError(f'SSH did not become available on localhost:{port}')
def wait_off(name,timeout=90):
 deadline=time.monotonic()+timeout
 while time.monotonic()<deadline:
  if domstate(name)=='shut off':return
  time.sleep(1)
 raise RuntimeError(f'{name} did not shut down; it was not force-stopped')
def shutdown(name):
 if domstate(name)=='shut off':return
 virsh('shutdown',name,capture_output=True);wait_off(name)
def cloud_seed(directory,instance,hostname,packages=None):
 directory.mkdir(parents=True,exist_ok=True)
 cfg={'hostname':hostname,'manage_etc_hosts':False,'ssh_pwauth':False,'disable_root':True,'users':[{'name':'trainee','uid':1000,'groups':['sudo','systemd-journal'],'shell':'/bin/bash','sudo':'ALL=(ALL) NOPASSWD:ALL','lock_passwd':True,'ssh_authorized_keys':[KEY.with_suffix('.pub').read_text().strip()]}]}
 if packages:
  cfg.update(package_update=True,packages=packages,runcmd=[['sh','-c','systemctl disable --now nginx cron || true'],['touch','/var/lib/devops-base-ready']])
 (directory/'user-data').write_text('#cloud-config\n'+json.dumps(cfg,indent=2)+'\n')
 (directory/'meta-data').write_text(json.dumps({'instance-id':instance,'local-hostname':hostname})+'\n')
 (directory/'network-config').write_text(json.dumps({'version':2,'ethernets':{'primary':{'match':{'name':'en*'},'dhcp4':True,'dhcp6':False}}})+'\n')
 run(['genisoimage','-quiet','-output',directory/'seed.iso','-volid','cidata','-joliet','-rock',directory/'user-data',directory/'meta-data',directory/'network-config'],capture_output=True)
 return directory/'seed.iso'
def domain_xml(name,disk,seed,port,memory=1024,cpus=1,domain_uuid=None):
 domain=ET.Element('domain',type='kvm')
 ET.SubElement(domain,'name').text=name
 ET.SubElement(domain,'uuid').text=domain_uuid or str(uuid.uuid4())
 ET.SubElement(domain,'memory',unit='MiB').text=str(memory)
 ET.SubElement(domain,'vcpu').text=str(cpus)
 osnode=ET.SubElement(domain,'os');ET.SubElement(osnode,'type',arch='x86_64',machine='q35').text='hvm'
 ET.SubElement(osnode,'boot',dev='hd')
 features=ET.SubElement(domain,'features');ET.SubElement(features,'acpi');ET.SubElement(features,'apic')
 ET.SubElement(domain,'cpu',mode='host-passthrough')
 ET.SubElement(domain,'clock',offset='utc')
 for event,action in [('on_poweroff','destroy'),('on_reboot','restart'),('on_crash','destroy')]:ET.SubElement(domain,event).text=action
 devices=ET.SubElement(domain,'devices');ET.SubElement(devices,'emulator').text='/usr/bin/qemu-system-x86_64'
 for path,device,target,bus in [(disk,'disk','vda','virtio'),(seed,'seed','vdb','virtio')]:
  d=ET.SubElement(devices,'disk',type='file',device='disk')
  ET.SubElement(d,'driver',name='qemu',type='qcow2' if device=='disk' else 'raw')
  ET.SubElement(d,'source',file=str(path));ET.SubElement(d,'target',dev=target,bus=bus)
  if device=='seed':ET.SubElement(d,'readonly')
 interface=ET.SubElement(devices,'interface',type='user')
 ET.SubElement(interface,'mac',address='52:54:00:'+':'.join(hashlib.sha256(name.encode()).hexdigest()[i:i+2] for i in (0,2,4)))
 ET.SubElement(interface,'model',type='virtio');ET.SubElement(interface,'backend',type='passt')
 forward=ET.SubElement(interface,'portForward',proto='tcp',address='127.0.0.1');ET.SubElement(forward,'range',start=str(port),to='22')
 serial=ET.SubElement(devices,'serial',type='pty');ET.SubElement(serial,'target',port='0');ET.SubElement(serial,'log',file=str(STATE/(name+'-console.log')),append='on')
 console=ET.SubElement(devices,'console',type='pty');ET.SubElement(console,'target',type='serial',port='0')
 channel=ET.SubElement(devices,'channel',type='unix');ET.SubElement(channel,'target',type='virtio',name='org.qemu.guest_agent.0')
 rng=ET.SubElement(devices,'rng',model='virtio');ET.SubElement(rng,'backend',model='random').text='/dev/urandom'
 return ET.tostring(domain,encoding='unicode')
def define(name,disk,seed,port,memory=1024,cpus=1):
 existing=virsh('domuuid',name,check=False,capture_output=True)
 domain_uuid=existing.stdout.strip() if existing.returncode==0 else None
 path=STATE/(name+'.xml');path.write_text(domain_xml(name,disk,seed,port,memory,cpus,domain_uuid));virsh('define',path,capture_output=True)
def overlay(path,backing):
 if path.exists():raise RuntimeError(f'Refusing to overwrite existing disk: {path}')
 run(['qemu-img','create','-q','-f','qcow2','-F','qcow2','-b',backing,path],capture_output=True)
def reboot(name,port):
 old=ssh(port,'cat /proc/sys/kernel/random/boot_id',capture_output=True).stdout.strip()
 virsh('reboot',name,capture_output=True)
 deadline=time.monotonic()+180
 while time.monotonic()<deadline:
  time.sleep(2)
  result=ssh(port,'cat /proc/sys/kernel/random/boot_id',check=False,capture_output=True)
  if result.returncode==0 and result.stdout.strip()!=old:
   ssh(port,'systemctl is-system-running --wait',capture_output=True);return
 raise RuntimeError(f'{name} did not finish rebooting')
def read_config():return json.loads((STATE/'config.json').read_text())
def write_ssh(config):
 lines=[]
 for n,lab in config.items():
  lines.append(f'''Host lab{n}
 HostName 127.0.0.1
 Port {lab['port']}
 User trainee
 IdentityFile "{KEY}"
 IdentitiesOnly yes
 StrictHostKeyChecking accept-new
 UserKnownHostsFile "{STATE}/known_hosts"
''')
 (ROOT/'.lab/ssh_config').write_text('\n'.join(lines))
