#!/usr/bin/python3
import http.server, json, os, socketserver, urllib.parse, urllib.request, time
MODE=os.environ.get('MODE','echo')
class Handler(http.server.BaseHTTPRequestHandler):
 def do_GET(self):
  args=urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
  token=args.get('token',['hello'])[0]
  try:
   if MODE=='report':
    with open('/srv/reports/current.txt') as f: value=f.read().strip()
   elif MODE=='gateway':
    config=json.load(open(os.environ.get('SERVICE_CONFIG','/etc/service.json')))
    with urllib.request.urlopen(config['inventory_url']+'/?token='+urllib.parse.quote(token),timeout=2) as r: value=json.load(r)['value']
   elif MODE=='capacity':
    count=int(args.get('batch',['1'])[0]); handles=[]
    if not 1<=count<=100: raise ValueError('batch must be 1..100')
    try:
     for _ in range(count): handles.append(open('/dev/null'))
     value=f'{token}:{len(handles)}'
    finally:
     for f in handles:f.close()
   else:value=token
   body=json.dumps({'value':value}).encode();self.send_response(200)
  except Exception as e:
   print(f'{time.ctime()} request failed: {type(e).__name__}: {e}',flush=True)
   body=json.dumps({'error':'request could not be completed'}).encode();self.send_response(503)
  self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(body)
class Server(socketserver.TCPServer): allow_reuse_address=True
with Server(('127.0.0.1',int(os.environ.get('PORT','9000'))),Handler) as server:server.serve_forever()
