#!/usr/bin/python3
import json,subprocess,secrets,sys
n=int(open('/etc/incident').read())
def call(url):
 cmd=['curl','--noproxy','*','-fsS','--connect-timeout','2','--max-time','4',url]
 if n in (6,7):cmd=['sudo','-n','ip','netns','exec','client','runuser','-u','app','--']+cmd
 return subprocess.run(cmd,text=True,capture_output=True)
try:
 for _ in range(3):
  token=secrets.token_hex(12)
  hosts=['orders.svc.test','catalog.svc.test'] if n==6 else ['10.80.2.2'] if n==7 else ['checkout.lab.test']
  for host in hosts:
   url=(f'https://{host}:8443' if n==8 else f'http://{host}:8080')+'/?token='+token
   r=call(url)
   assert r.returncode==0 and json.loads(r.stdout)['value']==token
 if n==7:
  # The private administrative listener must remain reachable locally but not from clients.
  r=subprocess.run(['sudo','-n','ip','netns','exec','backend','curl','-fsS','http://127.0.0.1:9099/'],capture_output=True)
  assert r.returncode==0
  assert call('http://10.80.2.2:9099/').returncode!=0
 print('PASS: customer acceptance checks passed. Use labctl durable to check reboot persistence.')
except (AssertionError,ValueError,KeyError):
 print('FAIL: customer acceptance checks are not satisfied.');sys.exit(1)
