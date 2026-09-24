import json, os, pathlib, subprocess, sys
n=int(sys.argv[1]); assert 1<=n<=5
from systemd_common import setup, program
P=pathlib.Path
def write(p,s): P(p).parent.mkdir(parents=True,exist_ok=True);P(p).write_text(s)
content=json.loads(P('/tmp/lab/content.json').read_text());title,symptom,criteria=content['problems'][n-1]
write('/etc/lab-scenario',str(n))
write('/home/trainee/problem.md',f'''# Incident {n}: {title}

{symptom}

## Recovery criteria
{criteria}
The fix must survive a service restart and a machine restart.
Keep the real services and their behavior; do not replace them with a canned response.

## Working environment
You are `trainee`, with passwordless sudo. Services are managed by systemd.
Start with your own observations. Service logs are in the journal; application-specific files may also be in /var/log/lab.
Run `verify` for an acceptance check (the scheduled export check may take 75 seconds).
Verify briefly changes test data in exercises 2 and 5, then restores it.
Use `systemctl` to manage services and `journalctl` to inspect their logs.
Hints are available on the host through `./labctl hint {n} 1`.
''')
write('/etc/ssh/sshd_config','''Port 22
ListenAddress 0.0.0.0
PermitRootLogin no
PasswordAuthentication no
KbdInteractiveAuthentication no
PubkeyAuthentication yes
UsePAM no
AllowUsers trainee
AllowTcpForwarding no
X11Forwarding no
PermitTunnel no
Subsystem sftp internal-sftp
''')
setup()
program('sshd','/usr/sbin/sshd -D -e')
if n==1:
 program('application','/usr/bin/python3 -u /opt/service/service.py','app','PORT="9000",MODE="echo"')
 write('/etc/nginx/nginx.conf','''user www-data;
pid /run/nginx.pid;
events { worker_connections 128; }
http {
 access_log /var/log/lab/nginx.access.log;
 error_log /var/log/lab/nginx.error.log;
 server { listen 127.0.0.1:8080; location / { proxy_pass http://127.0.0.1:9001; } }
}
''')
 program('nginx','/usr/sbin/nginx -g "daemon off;"')
elif n==2:
 subprocess.run('groupadd report-readers && usermod -aG report-readers app && usermod -aG report-readers reporter', shell=True, check=True)
 write('/srv/reports/current.txt','Report delivery 202: awaiting customer access\n')
 write('/etc/default/report-publisher','CREATE_MASK=0077\n')
 subprocess.run('chown reporter:report-readers /srv/reports /srv/reports/current.txt && chmod 2750 /srv/reports && chmod 600 /srv/reports/current.txt', shell=True, check=True)
 program('reports','/usr/bin/python3 -u /opt/service/service.py','app','PORT="8080",MODE="report"')
elif n==3:
 write('/etc/service.json','{"inventory_url":"http://inventory.internal:9090"}\n')
 program('inventory','/usr/bin/python3 -u /opt/service/service.py','app','PORT="9090",MODE="echo"')
 program('gateway','/usr/bin/python3 -u /opt/service/service.py','app','PORT="8080",MODE="gateway",http_proxy="http://127.0.0.1:3128",no_proxy="localhost,127.0.0.1"')
elif n==4:
 write('/etc/default/processor','OPEN_FILES=32\n')
 write('/usr/local/bin/start-processor','#!/bin/sh\nset -eu\n. /etc/default/processor\nulimit -n "$OPEN_FILES"\nexec /usr/bin/python3 -u /opt/service/service.py\n')
 os.chmod('/usr/local/bin/start-processor',0o755)
 program('processor','/usr/local/bin/start-processor','app','PORT="8080",MODE="capacity"')
else:
 write('/srv/orders/current.json','{"batch":"today-01","amounts":[10,20,7]}\n')
 write('/srv/exports/current.json','{"batch":"yesterday","total":0,"generated_at":0}\n')
 subprocess.run('chown -R reporter:reporter /srv/orders /srv/exports && chmod 750 /srv/orders /srv/exports && chmod 640 /srv/orders/current.json /srv/exports/current.json', shell=True, check=True)
 write('/etc/cron.d/report-export','SHELL=/bin/sh\nPATH=/usr/bin:/bin\n* * * * * reporter export-report >> /var/log/lab/export.log 2>&1\n')
 write('/var/log/lab/export.log','')
 subprocess.run('chown reporter:reporter /var/log/lab/export.log', shell=True, check=True)
 program('cron','/usr/sbin/cron -f')
