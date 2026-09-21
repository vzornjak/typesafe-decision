#!/usr/bin/env python3
"""Offline Minis relay contract test; no model call."""
import hashlib,hmac,json,os,tempfile,threading,urllib.request,urllib.error,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
import main_relay as client
from http.server import HTTPServer

def main():
 checks=[]
 def check(name,ok):assert ok,name;checks.append(name)
 with tempfile.TemporaryDirectory() as td:
  secret=Path(td)/'secret';secret.write_bytes(b'x'*48)
  old=os.environ.get('PHASE2_RELAY_SECRET_FILE');os.environ['PHASE2_RELAY_SECRET_FILE']=str(secret)
  import relay_minis as srv
  srv.SECRET=secret.read_bytes();srv.NONCES.clear()
  server=HTTPServer(('127.0.0.1',0),srv.Handler)
  th=threading.Thread(target=server.serve_forever,daemon=True);th.start()
  url=f'http://127.0.0.1:{server.server_address[1]}/v1/main'
  os.environ['PHASE2_RELAY_URL']=url
  cfg=json.loads((ROOT/'config/execution.json').read_text());system=(ROOT/'prompts/main-system.md').read_text()
  try:
   request=urllib.request.Request(url,data=b'{}',method='POST')
   try:urllib.request.urlopen(request,timeout=3);raise AssertionError('no HMAC passed')
   except urllib.error.HTTPError as e:check('reject unsigned request',e.code==403)
   original=srv.subprocess.run
   def fake(cmd,**kwargs):
    msg=json.loads(Path(cmd[cmd.index('--input')+1]).read_text())
    check('exact user message',msg['messages'][0]['content']=='synthetic prompt')
    return type('P',(),{'returncode':0,'stdout':json.dumps({'ok':True,'data':{'model_id':cfg['main']['model'],'stop_reason':'end_turn','output_text':'synthetic response','usage':{'input_tokens':15,'output_tokens':4}}})})()
   srv.subprocess.run=fake
   text,usage,model=client.call('synthetic prompt',cfg,system)
   check('model and usage round trip',text=='synthetic response' and usage['input_tokens']==15 and model==cfg['main']['model'])
   check('relay reports uncached buckets explicitly',usage['cache_read_input_tokens']==0 and usage['cache_creation_input_tokens']==0)
   check('one successful nonce',len(srv.NONCES)==1)
  finally:
   srv.subprocess.run=original;server.shutdown();server.server_close();th.join(timeout=3)
   if old is None:os.environ.pop('PHASE2_RELAY_SECRET_FILE',None)
   else:os.environ['PHASE2_RELAY_SECRET_FILE']=old
   os.environ.pop('PHASE2_RELAY_URL',None)
 print(json.dumps({'ok':True,'tests':len(checks),'checks':checks}));return 0
if __name__=='__main__':sys.exit(main())
