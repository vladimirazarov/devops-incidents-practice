#!/usr/bin/python3
import http.server,json,os,urllib.parse
class Handler(http.server.BaseHTTPRequestHandler):
 def do_GET(self):
  token=urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get('token',[''])[0]
  data=json.dumps({'value':token,'service':os.environ.get('SERVICE','orders')}).encode()
  self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
http.server.ThreadingHTTPServer(('0.0.0.0',int(os.environ.get('PORT','8080'))),Handler).serve_forever()
