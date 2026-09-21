#!/usr/bin/env python3
"""Offline positive/negative contract checks for supplementary output seal."""
import contextlib,io,json,tempfile,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
import scored_runner as runner
import validate_outputs as validator

def task():return json.loads((ROOT/'public/p2-dev-en-01.json').read_text())
def rank(obj):
 ids=[c['id'] for c in obj['candidates']]
 return {'model_requested':'jev-1.13.0','models_served':['jev-1.13.0'],'mode':'shortlist' if obj.get('mode')=='shortlist' else 'winner','decision':'selected' if obj.get('mode')=='shortlist' else ids[0], 'selection':obj.get('selection'),'selected':ids[:4], 'ranking':[{'id':cid,'eligible':True,'score':.95-i*.02} for i,cid in enumerate(ids)], 'usage':{'input_tokens':100,'output_tokens':20},'total_usage':{'input_tokens':100,'output_tokens':20},'api_attempts':1,'api_responses_received':1,'api_calls':1,'warnings':[]}
def main_model(text,config):return 'Offline synthetic answer [c01]',{'input_tokens':500,'output_tokens':10,'cache_read_input_tokens':0,'cache_creation_input_tokens':0},config['main']['model']
def check(name,value):
 if not value:raise AssertionError(name)
 return name

def main():
 checks=[]
 with tempfile.TemporaryDirectory() as td:
  root=Path(td); inputs=root/'runner-inputs';inputs.mkdir()
  for i in range(16):
   row=task();row['task_id']=f'p2-score-en-{i+1:02d}';(inputs/f"{row['task_id']}.json").write_text(json.dumps(row))
  old_inputs=runner.gate.RUNNER_INPUTS;old_lock=runner.gate.INPUT_LOCK;old_preflight=runner.preflight;old_artifact=runner.artifact
  runner.gate.RUNNER_INPUTS=inputs;runner.gate.INPUT_LOCK=root/'inputs.lock.json';runner.gate.INPUT_LOCK.write_text('{}');runner.preflight=lambda: {'offline_test':True}
  def synthetic_artifact(task,arm,rep,design,execution,rank_fn,main_fn,attempt=None):
   row=old_artifact(task,arm,rep,design,execution,rank_fn,main_fn,attempt)
   if arm!='A_no_rank':
    row['accounting_status']='complete'
    row['accounting_attempts']=[{'provider':'jev','status':'accepted','usage_complete':True,'usage':{'input_tokens':100,'output_tokens':20}} for _ in range(1)]+row['accounting_attempts']
   return row
  runner.artifact=synthetic_artifact
  try:
   out=root/'outputs'
   with contextlib.redirect_stdout(io.StringIO()):res=runner.execute(out,rank_fn=rank,main_fn=main_model)
   checks.append(check('160 successful rows',res['outputs']==160))
   checks.append(check('positive output gate',validator.validate(out)['ok']))
   p=out/'p2-score-en-01__C_shortlist_default__rep1.json';original=p.read_text();x=json.loads(original)
   x['usage']['main_input_tokens']=None;p.write_text(json.dumps(x));checks.append(check('unknown usage rejected',not validator.validate(out)['ok']));p.write_text(original)
   x=json.loads(original);x['accounting_status']='unknown';p.write_text(json.dumps(x));checks.append(check('unknown billed attempt rejected',not validator.validate(out)['ok']));p.write_text(original)
   x=json.loads(original);x['usage']['main_cache_read_input_tokens']=None;p.write_text(json.dumps(x));checks.append(check('unknown cache usage rejected',not validator.validate(out)['ok']));p.write_text(original)
   x=json.loads(original);x['selection']['prompt_sha256']='0'*64;p.write_text(json.dumps(x));checks.append(check('forged prompt hash rejected',not validator.validate(out)['ok']));p.write_text(original)
   x=json.loads(original);x['selection']['candidate_order']=list(reversed(x['selection']['candidate_order']));p.write_text(json.dumps(x));checks.append(check('candidate order drift rejected',not validator.validate(out)['ok']));p.write_text(original)
   x=json.loads(original);x['selection']['status']='failed';p.write_text(json.dumps(x));checks.append(check('failed run rejected',not validator.validate(out)['ok']));p.write_text(original)
   p.unlink();checks.append(check('missing row rejected',not validator.validate(out)['ok']))
  finally:runner.artifact=old_artifact;runner.gate.RUNNER_INPUTS=old_inputs;runner.gate.INPUT_LOCK=old_lock;runner.preflight=old_preflight
 print(json.dumps({'ok':True,'tests':len(checks),'checks':checks}));return 0
if __name__=='__main__':sys.exit(main())
