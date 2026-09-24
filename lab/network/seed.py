#!/usr/bin/python3
"""Instructor provisioning. Never installed into the learner VM."""
import pathlib,subprocess,sys,shutil
P=pathlib.Path;n=int(sys.argv[1])
def write(path,text,mode=0o644):
 p=P(path);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text);p.chmod(mode)
def run(*cmd):subprocess.run(cmd,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
def unit(name,command,user='root',after='',oneshot=False):
 write('/etc/systemd/system/'+name+'.service',f'''[Unit]
Description={name.replace('-',' ').title()}
After=network.target {after}
{'Requires='+after if after else ''}
[Service]
Type={'oneshot' if oneshot else 'simple'}
User={user}
ExecStart={command}
{'RemainAfterExit=yes' if oneshot else 'Restart=on-failure'}
[Install]
WantedBy=multi-user.target
''')
 run('systemctl','enable',name)
run('systemctl','disable','--now','dnsmasq','nginx','cron')
if subprocess.run(['systemctl','is-failed','--quiet','dnsmasq.service']).returncode==0:
 run('systemctl','reset-failed','dnsmasq.service')
write('/etc/incident',str(n)+'\n')
write('/etc/systemd/journald.conf.d/lab.conf','[Journal]\nStorage=persistent\nSystemMaxUse=64M\n')
P('/var/log/journal').mkdir(exist_ok=True)
shutil.copy('/tmp/lab/network/app.py','/opt/service/network-app.py')
shutil.copy('/tmp/lab/network/verify.py','/usr/local/bin/verify');P('/usr/local/bin/verify').chmod(0o755)
if n in (6,7):
 write('/usr/local/sbin/site-network','''#!/bin/bash
set -euo pipefail
for ns in client backend; do ip netns add "$ns"; ip -n "$ns" link set lo up; done
ip link add lan-client type veth peer name eth0 netns client
ip link add lan-backend type veth peer name eth0 netns backend
ip address add 10.80.1.1/24 dev lan-client
ip address add 10.80.2.1/24 dev lan-backend
ip link set lan-client up
ip link set lan-backend up
ip -n client address add 10.80.1.2/24 dev eth0
ip -n backend address add 10.80.2.2/24 dev eth0
ip -n client link set eth0 up
ip -n backend link set eth0 up
ip -n client route add default via 10.80.1.1
ip -n backend route add default via 10.80.2.1
sysctl -w net.ipv4.ip_forward=1
''',0o755)
 unit('site-network','/usr/local/sbin/site-network',oneshot=True)
 unit('orders-api','/usr/sbin/ip netns exec backend /usr/sbin/runuser -u app -- /usr/bin/python3 /opt/service/network-app.py',after='site-network.service')
 url='http://orders.svc.test:8080/' if n==6 else 'http://10.80.2.2:8080/'
 write('/usr/local/bin/probe',f'''#!/bin/bash
set -euo pipefail
exec sudo -n ip netns exec client runuser -u app -- curl --noproxy '*' --connect-timeout 3 --max-time 5 -fsS --get --data-urlencode "token=${{1:-sample}}" '{url}'
''',0o755)
 if n==6:
  write('/etc/netns/client/resolv.conf','nameserver 10.80.1.1\noptions timeout:1 attempts:1\n')
  write('/etc/service-discovery/records','10.80.2.99 orders.svc.test catalog.svc.test\n')
  write('/etc/service-discovery/dnsmasq.conf','no-resolv\nno-hosts\nbind-interfaces\nlisten-address=10.80.1.1\naddn-hosts=/etc/service-discovery/records\nlocal=/svc.test/\nlog-queries\nlog-facility=-\n')
  unit('service-discovery','/usr/sbin/dnsmasq --keep-in-foreground --conf-file=/etc/service-discovery/dnsmasq.conf',after='site-network.service')
 else:
  unit('admin-api','/usr/sbin/ip netns exec backend /usr/sbin/runuser -u app -- /usr/bin/env PORT=9099 /usr/bin/python3 /opt/service/network-app.py',after='site-network.service')
  write('/etc/site-firewall.nft','''table inet site {
 chain forward {
  type filter hook forward priority 0; policy drop;
  ct state established,related counter accept
  iifname "lan-client" oifname "lan-backend" ip daddr 10.80.2.2 tcp dport 80 counter accept
  ip protocol icmp counter accept
  counter drop
 }
}
''')
  unit('site-firewall','/usr/sbin/nft -f /etc/site-firewall.nft',after='site-network.service',oneshot=True)
else:
 unit('orders-api','/usr/bin/python3 /opt/service/network-app.py',user='app')
 with open('/etc/hosts','a') as f:f.write('\n127.0.0.1 checkout.lab.test\n')
 certdir=P('/etc/pki/checkout');certdir.mkdir(parents=True,exist_ok=True)
 def openssl(*args):run('openssl',*args)
 openssl('req','-x509','-newkey','rsa:2048','-nodes','-keyout',str(certdir/'ca.key'),'-out',str(certdir/'ca.crt'),'-days','3650','-subj','/CN=Practice Root CA')
 for name,host in [('release-a','previous.lab.test'),('release-b','checkout.lab.test')]:
  prefix=str(certdir/name)
  openssl('req','-new','-newkey','rsa:2048','-nodes','-keyout',prefix+'.key','-out',prefix+'.csr','-subj','/CN='+host)
  write(prefix+'.ext',f'subjectAltName=DNS:{host}\nextendedKeyUsage=serverAuth\nbasicConstraints=CA:FALSE\n')
  openssl('x509','-req','-in',prefix+'.csr','-CA',str(certdir/'ca.crt'),'-CAkey',str(certdir/'ca.key'),'-CAcreateserial','-out',prefix+'.crt','-days','3650','-extfile',prefix+'.ext')
  P(prefix+'.key').chmod(0o600);P(prefix+'.csr').unlink();P(prefix+'.ext').unlink()
 shutil.copy(certdir/'ca.crt','/usr/local/share/ca-certificates/practice-root.crt');run('update-ca-certificates')
 (certdir/'ca.key').unlink();(certdir/'ca.srl').unlink(missing_ok=True)
 write('/etc/nginx/nginx.conf','''user www-data;
worker_processes auto;
pid /run/nginx.pid;
events { worker_connections 256; }
http {
 access_log /var/log/nginx/access.log;
 error_log /var/log/nginx/error.log;
 server {
  listen 8443 ssl;
  server_name checkout.lab.test;
  ssl_certificate /etc/pki/checkout/release-a.crt;
  ssl_certificate_key /etc/pki/checkout/release-a.key;
  location / { proxy_pass http://127.0.0.1:8080; proxy_set_header Host $host; }
 }
}
''')
 run('systemctl','enable','nginx')
 write('/usr/local/bin/probe','''#!/bin/bash
set -euo pipefail
exec curl --noproxy '*' --connect-timeout 3 --max-time 5 -fsS --get --data-urlencode "token=${1:-sample}" https://checkout.lab.test:8443/
''',0o755)
problems={
6:('The order desk has gone quiet','The branch team cannot retrieve order information after a routine infrastructure update. The API owner reports that the service is running.', '''From the client environment, both http://orders.svc.test:8080/ and http://catalog.svc.test:8080/ must return JSON with value equal to the token query parameter. Use `probe YOUR_VALUE` for the order-desk request. The client environment is the Linux network namespace named client; the application runs in backend. You can run other client commands with `sudo ip netns exec client COMMAND`.

Keep the service names, client environment and existing API. Do not add static client host-file entries or substitute a response. Recovery must survive a VM reboot.'''),
7:('The branch is waiting','The branch cannot submit its usual requests. A local check at the service site succeeds, but the branch sees no useful response.', '''From the client environment, http://10.80.2.2:8080/?token=YOUR_VALUE must return JSON with value equal to YOUR_VALUE. Use `probe YOUR_VALUE` to reproduce the branch request. The client environment is the Linux network namespace named client; the service environment is backend. Other client commands can run through `sudo ip netns exec client COMMAND`.

The backend administrative endpoint on port 9099 must remain available inside backend and inaccessible from client. Preserve the existing addresses, separate environments and services. Do not disable traffic policy wholesale or substitute a response. Recovery must survive a VM reboot.'''),
8:('Checkout is unavailable','Customers cannot use the checkout endpoint following a deployment. The application team says the backend is healthy.', '''https://checkout.lab.test:8443/?token=YOUR_VALUE must return JSON with value equal to YOUR_VALUE through the existing edge service. Use `probe YOUR_VALUE` to reproduce the request.

Keep the hostname, HTTPS, normal client validation, existing trusted authority and backend application. Do not bypass validation or substitute a response. Recovery must survive a VM reboot.''')}
title,symptom,criteria=problems[n]
write('/home/trainee/problem.md',f'# {title}\n\n{symptom}\n\n## Required outcome\n\n{criteria}\n\nRun `verify` to check recovery.\n')
run('chown','trainee:trainee','/home/trainee/problem.md')
run('systemctl','daemon-reload');run('systemctl','restart','systemd-journald')
for service in (['site-network','orders-api','service-discovery'] if n==6 else ['site-network','site-firewall','orders-api','admin-api'] if n==7 else ['orders-api','nginx']):run('systemctl','start',service)
