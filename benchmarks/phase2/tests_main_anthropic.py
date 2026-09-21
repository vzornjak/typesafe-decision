#!/usr/bin/env python3
"""Offline direct-MAIN transport contract checks; no provider call."""
import io,json,os,sys,urllib.error
from pathlib import Path
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
import main_anthropic as m
class Response:
    def __init__(self, body):self.body=json.dumps(body).encode()
    def __enter__(self):return self
    def __exit__(self,*args):return False
    def read(self,n):return self.body

def main():
    cfg=json.load(open(ROOT/'config/execution.json'));old=os.environ.get('ANTHROPIC_API_KEY');os.environ['ANTHROPIC_API_KEY']='test-key-not-real'
    checks=[]
    def check(name,condition):
        assert condition,name;checks.append(name)
    try:
        def stub(request, timeout):
            d=json.loads(request.data);check('exact model and temperature',d['model']==cfg['main']['model'] and d['temperature']==0)
            check('system and user fidelity',d['system']=='system sample' and d['messages'][0]['content']=='user sample')
            return Response({'model':d['model'],'stop_reason':'end_turn','content':[{'type':'text','text':'test answer'}],
                             'usage':{'input_tokens':12,'output_tokens':3}})
        a,u,model=m.call('user sample',cfg,'system sample',stub)
        check('parsed response usage',a=='test answer' and u['input_tokens']==12 and model==cfg['main']['model'])
        try:m.parse({'model':cfg['main']['model'],'stop_reason':'max_tokens','content':[{'type':'text','text':'cut'}],'usage':{'input_tokens':5,'output_tokens':3}},cfg['main']['model']);raise AssertionError('accepted truncation')
        except m.MainTransportError as e:check('truncation retains known usage',e.usage['input_tokens']==5)
        def failed(request,timeout):raise urllib.error.HTTPError(m.API,429,'limited',{},io.BytesIO(b'{}'))
        try:m.call('user sample',cfg,'system sample',failed);raise AssertionError('accepted HTTP failure')
        except m.MainTransportError as e:check('HTTP failure usage unknown',e.usage is None)
    finally:
        if old is None:os.environ.pop('ANTHROPIC_API_KEY',None)
        else:os.environ['ANTHROPIC_API_KEY']=old
    print(json.dumps({'ok':True,'tests':len(checks),'checks':checks}));return 0
if __name__=='__main__':raise SystemExit(main())
