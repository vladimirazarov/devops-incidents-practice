#!/usr/bin/env python3
import argparse,datetime,pathlib,sys,platform

from runtime import *
parser=argparse.ArgumentParser(description='Local Linux VM practice lab')
parser.add_argument('command',choices=['start','stop','restart','status','ssh','verify','durable','reset','hint','console','test'])
parser.add_argument('incident',nargs='?',type=int,choices=range(1,9))
parser.add_argument('level',nargs='?',type=int,choices=range(1,4))
args=parser.parse_args()
backend=os.environ.get('LAB_BACKEND') or ('lima' if platform.system()=='Darwin' else 'libvirt' if (STATE/'config.json').exists() else 'lima')
if backend not in ('lima','libvirt'):parser.error('LAB_BACKEND must be lima or libvirt')
if args.command not in ('start','stop','status','test') and args.incident is None:parser.error('This command requires an incident number')
if backend=='lima':
 import lima_backend
 try:lima_backend.main(args)
 except (RuntimeError,subprocess.CalledProcessError) as error:sys.exit(str(error))
 sys.exit(0)
if not (STATE/'config.json').exists():sys.exit('Run ./setup first.')
config=read_config()
if args.command not in ('start','stop','status','test') and args.incident is None:parser.error('This command requires an incident number')
selected=[str(args.incident)] if args.incident else list(config)
def start(lab):
 state=domstate(lab['name'])
 if state=='shut off':virsh('start',lab['name'],capture_output=True)
 elif state!='running':raise RuntimeError(f"Unexpected VM state: {state}")
 wait_ssh(lab['port'])
def reset(lab):
 shutdown(lab['name'])
 directory=pathlib.Path(lab['directory']);live=directory/'live.qcow2'
 archive=directory/'reset-history';archive.mkdir(exist_ok=True)
 stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
 replacement=directory/'replacement.qcow2';overlay(replacement,directory/'baseline.qcow2')
 live.rename(archive/(stamp+'.qcow2'));replacement.rename(live)
 start(lab)
 print('Fresh exercise restored. Previous disk retained in reset-history/.')
try:
 if args.command=='test':
  os.execv(sys.executable,[sys.executable,str(ROOT/'vm/test_exercises.py')]+([str(args.incident)] if args.incident else []))
 if args.command=='hint':
  if args.level is None:parser.error('Hint level 1, 2 or 3 is required')
  print((ROOT/f'instructor/hints/{args.incident}-{args.level}.md').read_text());sys.exit(0)
 for n in selected:
  lab=config[n];command=args.command
  if command=='status':print(f"lab{n}: {domstate(lab['name'])}; SSH 127.0.0.1:{lab['port']}")
  elif command=='start':start(lab);print(f'lab{n} ready')
  elif command=='stop':shutdown(lab['name']);print(f'lab{n} stopped; disk preserved')
  elif command=='restart':reboot(lab['name'],lab['port']);print(f'lab{n} rebooted')
  elif command=='reset':reset(lab)
  elif command=='console':os.execvp('virsh',['virsh','-c',URI,'console',lab['name']])
  elif command=='ssh':
   if domstate(lab['name'])!='running':sys.exit(f'lab{n} is stopped. Start it with: ./labctl start {n}')
   write_ssh(config);os.execvp('ssh',['ssh','-F',str(ROOT/'.lab/ssh_config'),f'lab{n}'])
  elif command in ('verify','durable'):
   ssh(lab['port'],'verify')
   if command=='durable':reboot(lab['name'],lab['port']);ssh(lab['port'],'verify')
except (RuntimeError,subprocess.CalledProcessError) as error:
 sys.exit(str(error))
