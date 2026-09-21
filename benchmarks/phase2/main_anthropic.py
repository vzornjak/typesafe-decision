#!/usr/bin/env python3
"""Direct Anthropic Messages transport for Phase 2 on isolated Docker hosts.
No credentials in files: ANTHROPIC_API_KEY is read at call time from environment.
"""
import json, os, urllib.request, urllib.error

API = 'https://api.anthropic.com/v1/messages'
VERSION = '2023-06-01'
class MainTransportError(RuntimeError):
    def __init__(self, code, usage=None):
        super().__init__(code)
        self.usage = usage

def usage_of(payload):
    if not isinstance(payload, dict) or not isinstance(payload.get('usage'), dict): return None
    u=payload['usage']; a=u.get('input_tokens'); b=u.get('output_tokens')
    if type(a) is not int or type(b) is not int or a<0 or b<0:return None
    return {'input_tokens':a,'output_tokens':b,
            'cache_creation_input_tokens':u.get('cache_creation_input_tokens',0),
            'cache_read_input_tokens':u.get('cache_read_input_tokens',0)}

def parse(payload, expected_model):
    usage=usage_of(payload)
    if not isinstance(payload, dict): raise MainTransportError('anthropic_invalid_envelope',usage)
    if payload.get('model')!=expected_model: raise MainTransportError('anthropic_model_drift',usage)
    if payload.get('stop_reason')!='end_turn': raise MainTransportError('anthropic_nonfinal_stop',usage)
    text=''.join(x.get('text','') for x in payload.get('content',[]) if isinstance(x,dict) and x.get('type')=='text')
    if not text.strip():raise MainTransportError('anthropic_empty_text',usage)
    if usage is None:raise MainTransportError('anthropic_usage_missing',usage)
    return text,usage,payload['model']

def call(prompt_text, execution, system_text, transport=None):
    key=os.environ.get('ANTHROPIC_API_KEY')
    if not key:raise MainTransportError('anthropic_key_missing')
    request_body={'model':execution['main']['model'],'max_tokens':execution['main']['max_output_tokens'],
                  'temperature':execution['main']['temperature'],'system':system_text,
                  'messages':[{'role':'user','content':prompt_text}]}
    payload=json.dumps(request_body,ensure_ascii=False).encode()
    req=urllib.request.Request(API,data=payload,headers={'x-api-key':key,'anthropic-version':VERSION,'content-type':'application/json'},method='POST')
    transport=transport or urllib.request.urlopen
    try:
        with transport(req,timeout=execution.get('main_request_timeout_seconds',120)) as response:
            body=response.read(2_000_000)
    except urllib.error.HTTPError as exc:
        try: parsed=json.loads(exc.read(2_000_000))
        except Exception: parsed={}
        raise MainTransportError('anthropic_http_'+str(exc.code),usage_of(parsed)) from None
    try: parsed=json.loads(body)
    except Exception: raise MainTransportError('anthropic_unparseable_response') from None
    return parse(parsed,execution['main']['model'])
