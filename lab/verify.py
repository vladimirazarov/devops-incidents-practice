#!/usr/bin/python3
"""Observable acceptance checks. Full solutions live outside the image."""
import json, os, pathlib, secrets, stat, subprocess, sys, time, urllib.request
if os.geteuid()!=0:
 os.execvp('sudo',['sudo','/usr/local/bin/verify',*sys.argv[1:]])
P=pathlib.Path
n=int(P('/etc/lab-scenario').read_text())
def require(ok,message):
 if not ok: raise RuntimeError(message)
def request(path):
 opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
 with opener.open('http://127.0.0.1:8080/'+path,timeout=4) as r:
  require(r.status==200,'Endpoint did not return HTTP 200')
  return json.load(r)['value']
def unprivileged(name):
 pid=int(subprocess.check_output(['systemctl','show','--property=MainPID','--value',name+'.service'],text=True).strip())
 require(pid>0,'Required service is not running')
 status=P(f'/proc/{pid}/status').read_text()
 uid=next(l for l in status.splitlines() if l.startswith('Uid:')).split()[1:]
 require(all(int(x)!=0 for x in uid),'Service must run without root privileges')
def private(path):
 require(stat.S_IMODE(P(path).stat().st_mode)&7==0,'Report paths must deny access to other users')
token=secrets.token_hex(12)
try:
 if n in (1,3):
  for _ in range(3):
   value=secrets.token_hex(12)
   require(request('?token='+value)==value,'Response did not reflect the requested value')
  if n==1:
   require(subprocess.run(['nginx','-t'],capture_output=True).returncode==0,'nginx configuration does not validate')
   unprivileged('application')
  else:
   require(urllib.parse.urlparse(json.loads(P('/etc/service.json').read_text())['inventory_url']).hostname=='inventory.internal','Preserve the inventory hostname contract')
   unprivileged('gateway');unprivileged('inventory')
 elif n==2:
  target=P('/srv/reports/current.txt');old=target.read_bytes()
  try:
   for _ in range(2):
    fresh=secrets.token_hex(12)
    result=subprocess.run(['runuser','-u','reporter','--','/usr/local/bin/publish-report',fresh],capture_output=True)
    require(result.returncode==0,'A normal report delivery did not complete')
    require(request('')==fresh,'Endpoint did not return the newly delivered report')
   private('/srv/reports');private(target);unprivileged('reports')
   import pwd
   require(target.stat().st_uid==pwd.getpwnam('reporter').pw_uid,'Report delivery must retain the reporter identity')
   require(subprocess.run(['runuser','-u','nobody','--','cat',str(target)],capture_output=True).returncode!=0,'Unrelated users can read the report')
  finally:target.write_bytes(old)
 elif n==4:
  for count in (1,50,80,2,80):
   require(request(f'?batch={count}&token={token}')==f'{token}:{count}','A representative batch failed')
  unprivileged('processor')
 else:
  source=P('/srv/orders/current.json');old=source.read_bytes();started=time.time()
  try:
   source.write_text(json.dumps({'batch':token,'amounts':[17,29,31]}))
   print('Checking the next scheduled run (up to 75 seconds)…',flush=True)
   deadline=time.monotonic()+75;passed=False
   while time.monotonic()<deadline:
    try:
     result=json.loads(P('/srv/exports/current.json').read_text())
     passed=result.get('batch')==token and result.get('total')==77 and result.get('generated_at',0)>=started
    except (OSError,ValueError):pass
    if passed:break
    time.sleep(2)
   require(passed,'A fresh, correct scheduled export did not arrive within 75 seconds')
   import pwd
   require(P('/srv/exports/current.json').stat().st_uid==pwd.getpwnam('reporter').pw_uid,'Export must be produced as reporter')
   private('/srv/exports');private('/srv/exports/current.json')
  finally:source.write_bytes(old)
 print('PASS — recovery criteria met. Next: test durability and explain the evidence from memory.')
except Exception as e:
 print(f'NOT YET — {e}',file=sys.stderr);sys.exit(1)
