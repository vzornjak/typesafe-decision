#!/usr/bin/env python3
"""Local-only Phase 2 MAIN relay: calls Minis provider without exporting OAuth.
Not a scored-run authorization; run only while Minis is active.
"""
import hashlib,hmac,json,os,subprocess,tempfile,time
from http.server import BaseHTTPRequestHandler,HTTPServer
from pathlib import Path
ROOT=Path(__file__).resolve().parent
CFG=json.loads((ROOT/'config/execution.json').read_text())
SYSTEM=(ROOT/'prompts/main-system.md').read_text()
assert hashlib.sha256(SYSTEM.encode()).hexdigest()==CFG['main']['system_prompt_sha256']
SECRET=Path(os.environ['PHASE2_RELAY_SECRET_FILE']).read_bytes().strip()
assert len(SECRET)>=32
NONCES=set()
MAX_BYTES=160000
class Server(HTTPServer):
 allow_reuse_address=True
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def send(self,status,obj):
  b=json.dumps(obj,separators=(',',':')).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
 def do_POST(self):
  if self.path!='/v1/main':return self.send(404,{'ok':False,'code':'wrong_path'})
  try:
   n=int(self.headers.get('Content-Length','0'))
   if not 0<n<=MAX_BYTES:return self.send(413,{'ok':False,'code':'invalid_length'})
   b=self.rfile.read(n)
   mac=self.headers.get('X-Relay-HMAC','')
   if not hmac.compare_digest(mac,hmac.new(SECRET,b,hashlib.sha256).hexdigest()):return self.send(403,{'ok':False,'code':'unauthorized'})
   x=json.loads(b)
   if set(x)!={'nonce','model','system_sha256','user_sha256','user','max_tokens','temperature'}:raise ValueError('bad_shape')
   nonce=x['nonce']
   if not isinstance(nonce,str) or len(nonce)!=32 or nonce in NONCES:raise ValueError('replay_or_bad_nonce')
   if x['model']!=CFG['main']['model'] or x['system_sha256']!=CFG['main']['system_prompt_sha256']:raise ValueError('contract_mismatch')
   if x['max_tokens']!=CFG['main']['max_output_tokens'] or x['temperature']!=CFG['main']['temperature']:raise ValueError('parameter_mismatch')
   user=x['user']
   if not isinstance(user,str) or not user or hashlib.sha256(user.encode()).hexdigest()!=x['user_sha256']:raise ValueError('prompt_mismatch')
   NONCES.add(nonce)
   with tempfile.TemporaryDirectory(prefix='p2-relay-') as td:
    p=Path(td)/'in.json';p.write_text(json.dumps({'messages':[{'role':'user','content':user}]},ensure_ascii=False))
    cmd=['minis-model-use','run','--model',x['model'],'--provider','Anthropic','--input',str(p),'--system-file',str(ROOT/'prompts/main-system.md'),'--max-tokens',str(x['max_tokens']),'--temperature',str(x['temperature'])]
    run=subprocess.run(cmd,capture_output=True,text=True,timeout=600)
   try:result=json.loads(run.stdout)
   except (ValueError,TypeError):return self.send(502,{'ok':False,'code':'unparseable_model_result','billing':'unknown'})
   d=result.get('data') or {}; usage=d.get('usage') if isinstance(d,dict) else None
   if run.returncode or result.get('ok') is not True:return self.send(502,{'ok':False,'code':'provider_failure','usage':usage,'billing':'unknown' if usage is None else 'reported'})
   if d.get('model_id')!=x['model'] or d.get('stop_reason')!='end_turn' or not isinstance(d.get('output_text'),str) or not d['output_text'].strip():
    return self.send(502,{'ok':False,'code':'provider_contract_failure','usage':usage,'billing':'unknown' if usage is None else 'reported'})
   if not isinstance(usage,dict) or any(type(usage.get(k)) is not int or usage[k]<0 for k in ('input_tokens','output_tokens')):return self.send(502,{'ok':False,'code':'invalid_usage','billing':'unknown'})
   return self.send(200,{'ok':True,'model_id':d['model_id'],'stop_reason':d['stop_reason'],'output_text':d['output_text'],'usage':usage,'user_sha256':x['user_sha256'],'system_sha256':x['system_sha256']})
  except (ValueError,TypeError) as e:return self.send(400,{'ok':False,'code':str(e)[:80]})
  except Exception:return self.send(502,{'ok':False,'code':'relay_error','billing':'unknown'})
if __name__=='__main__':Server(('127.0.0.1',18766),Handler).serve_forever()
