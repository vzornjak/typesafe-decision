#!/usr/bin/env python3
"""MAC-to-Minis relay client; only exact locked prompt and model are accepted."""
import hashlib,hmac,json,os,secrets,urllib.request,urllib.error
from pathlib import Path
class RelayError(RuntimeError):
 def __init__(self,reason,usage=None):super().__init__(reason);self.usage=usage

def call(user,execution,system):
 f=os.environ.get('PHASE2_RELAY_SECRET_FILE')
 if not f:raise RelayError('missing_relay_secret')
 secret=Path(f).read_bytes().strip()
 if len(secret)<32:raise RelayError('short_relay_secret')
 expected=execution['main']['system_prompt_sha256'];system_sha=hashlib.sha256(system.encode()).hexdigest()
 if system_sha!=expected:raise RelayError('system_hash_mismatch')
 obj={'nonce':secrets.token_hex(16),'model':execution['main']['model'],'system_sha256':system_sha,
      'user_sha256':hashlib.sha256(user.encode()).hexdigest(),'user':user,'max_tokens':execution['main']['max_output_tokens'],'temperature':execution['main']['temperature']}
 b=json.dumps(obj,ensure_ascii=False,separators=(',',':')).encode()
 req=urllib.request.Request(os.environ.get('PHASE2_RELAY_URL','http://host.docker.internal:18766/v1/main'),data=b,
      headers={'Content-Type':'application/json','X-Relay-HMAC':hmac.new(secret,b,hashlib.sha256).hexdigest()},method='POST')
 try:
  with urllib.request.urlopen(req,timeout=610) as r:d=json.loads(r.read(250000))
 except urllib.error.HTTPError as e:
  try:d=json.loads(e.read(250000))
  except Exception:d={}
  raise RelayError(d.get('code','http_error'),d.get('usage')) from None
 except Exception as e:raise RelayError(type(e).__name__) from None
 if d.get('ok') is not True or d.get('model_id')!=execution['main']['model'] or d.get('user_sha256')!=obj['user_sha256'] or d.get('system_sha256')!=system_sha:raise RelayError('relay_contract_mismatch',d.get('usage'))
 u=d.get('usage')
 if not isinstance(u,dict) or any(type(u.get(k)) is not int or u[k]<0 for k in ('input_tokens','output_tokens')):raise RelayError('relay_usage_invalid')
 if any(type(u.get(k,0)) is not int or u.get(k,0)<0 for k in ('cache_read_input_tokens','cache_creation_input_tokens')):raise RelayError('relay_cache_usage_invalid')
 u={'input_tokens':u['input_tokens'],'output_tokens':u['output_tokens'],
    'cache_read_input_tokens':u.get('cache_read_input_tokens',0),'cache_creation_input_tokens':u.get('cache_creation_input_tokens',0)}
 if d.get('stop_reason')!='end_turn' or not d.get('output_text'):raise RelayError('relay_incomplete',u)
 return d['output_text'],u,d['model_id']
