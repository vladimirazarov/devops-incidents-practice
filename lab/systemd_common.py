"""Shared systemd provisioning for fresh images and state-preserving migration."""
import json, os, pathlib, shlex
VM=os.environ.get("LAB_RUNTIME")=="vm"
P=pathlib.Path
def write(path,text):
 p=P(path);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
def enable(name):
 link=P('/etc/systemd/system/multi-user.target.wants')/(name+'.service')
 link.parent.mkdir(parents=True,exist_ok=True)
 if link.is_symlink() or link.exists():link.unlink()
 link.symlink_to('/etc/systemd/system/'+name+'.service')
def program(name,cmd,user='root',env=''):
 if name=='sshd':name='ssh'
 if VM and name=='ssh':return
 extra='Requires=lab-prepare.service\nAfter=lab-prepare.service\n' if name=='ssh' else ''
 lexer=shlex.shlex(env,posix=True);lexer.whitespace=',';lexer.whitespace_split=True;lexer.commenters=''
 environment=''.join('Environment='+json.dumps(value)+'\n' for value in lexer if value)
 reload='ExecReload=/usr/sbin/nginx -s reload\n' if name=='nginx' else ''
 write('/etc/systemd/system/'+name+'.service',f'''[Unit]
Description={name.capitalize()} service
After=network.target
{extra}
[Service]
Type=simple
User={user}
{environment}ExecStart={cmd}
{reload}Restart=on-failure
RestartSec=2
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
''')
 enable(name)
def setup():
 # Package defaults must not start services unrelated to the selected exercise.
 for name in (('nginx','cron','supervisor') if VM else ('nginx','cron','ssh','supervisor')):
  link=P('/etc/systemd/system/multi-user.target.wants')/(name+'.service')
  if link.is_symlink() or link.exists():link.unlink()
 if VM:
  write('/etc/systemd/journald.conf.d/lab.conf','[Journal]\nStorage=persistent\nSystemMaxUse=64M\n')
  P('/var/log/journal').mkdir(parents=True,exist_ok=True)
 else:
  write('/etc/systemd/system/lab-prepare.service','''[Unit]
 Description=Prepare SSH access
 Before=ssh.service

 [Service]
 Type=oneshot
 ExecStart=/usr/local/bin/lab-prepare
 RemainAfterExit=yes
 ''')
  write('/etc/systemd/journald.conf.d/lab.conf','[Journal]\nStorage=persistent\nSystemMaxUse=32M\nRuntimeMaxUse=8M\n')
  P('/var/log/journal').mkdir(parents=True,exist_ok=True)
  write('/etc/machine-id','')
  dbus=P('/var/lib/dbus/machine-id')
  if dbus.exists() or dbus.is_symlink():dbus.unlink()
  dbus.parent.mkdir(parents=True,exist_ok=True);dbus.symlink_to('/etc/machine-id')
 conf=P('/etc/ssh/sshd_config')
 if conf.exists():conf.write_text(conf.read_text().replace('UsePAM no','UsePAM yes'))
 target=P('/etc/systemd/system/default.target')
 if target.exists() or target.is_symlink():target.unlink()
 target.symlink_to('/lib/systemd/system/multi-user.target')
