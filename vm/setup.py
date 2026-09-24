#!/usr/bin/env python3
"""Install selected fresh labs; never reseed an existing completed installation."""
import argparse,os,pathlib,platform,shutil,subprocess,sys
from bootstrap import ROOT,image,keypair

def main():
 if sys.version_info<(3,11):raise RuntimeError('Python 3.11 or later is required.')
 parser=argparse.ArgumentParser(description='Install fresh Linux VM labs. Default: lab 1 only.')
 parser.add_argument('incidents',nargs='*',type=int,choices=range(1,9))
 parser.add_argument('--all',action='store_true',help='Install all eight labs (one at a time is lighter)')
 default='libvirt' if (ROOT/'.lab/vm/config.json').exists() and platform.system()=='Linux' else 'lima'
 parser.add_argument('--backend',choices=['lima','libvirt'],default=os.environ.get('LAB_BACKEND',default))
 args=parser.parse_args();selected=list(range(1,9)) if args.all else args.incidents or [1]
 if args.backend=='lima':
  from lima_backend import setup
  setup(selected)
 else:
  if platform.system()!='Linux' or platform.machine()!='x86_64':raise RuntimeError('Legacy libvirt setup requires x86_64 Linux; use Lima on this host.')
  for binary in ('virsh','qemu-img','qemu-system-x86_64','passt','genisoimage','ssh','ssh-keygen'):
   if not shutil.which(binary):raise RuntimeError('Missing '+binary+'. See docs/SETUP.md.')
  keypair();image('x86_64',ROOT/'.lab/vm/base')
  subprocess.run([sys.executable,str(ROOT/'vm/provision.py'),*map(str,selected)],check=True)
if __name__=='__main__':
 try:main()
 except (RuntimeError,subprocess.CalledProcessError) as error:sys.exit(str(error))
