#!/usr/bin/env python3
"""Offline scored-runner contract tests. No API calls or gold files."""
import importlib.util,json,tempfile,sys,contextlib,io
from pathlib import Path
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('scored_runner',ROOT/'scored_runner.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
checks=[]
def check(name,condition):
 checks.append(name)
 if not condition:raise AssertionError(name)
def task():
 return json.loads((ROOT/'public'/'p2-dev-en-01.json').read_text())
def stub_rank(obj):
 ids=[c['id'] for c in obj['candidates']]
 return {'model_requested':'jev-1.13.0','models_served':['jev-1.13.0'],'mode':'shortlist' if obj.get('mode')=='shortlist' else 'winner','selection':obj.get('selection'),'decision':'selected' if obj.get('mode')=='shortlist' else ids[0],
         'selected':ids[:4], 'ranking':[{'id':cid,'eligible':True,'score':.99-i*.03} for i,cid in enumerate(ids)],
         'usage':{'input_tokens':100,'output_tokens':20},'warnings':[]}
def stub_main(text,config):return ('Synthetic response [c01]',{'input_tokens':500,'output_tokens':8},config['main']['model'])
def main():
 t=task();t['task_id']='p2-score-en-01'
 design=json.loads((ROOT/'config'/'design.json').read_text());execution=json.loads((ROOT/'config'/'execution.json').read_text())
 check('different scored repetition seeds',r.seed(t['task_id'],'B_winner_top8',1)!=r.seed(t['task_id'],'B_winner_top8',2))
 check('different arm seeds',r.seed(t['task_id'],'B_winner_top8',1)!=r.seed(t['task_id'],'C_shortlist_default',1))
 check('baseline retains exact corpus order',r.candidates(t,'A_no_rank',0)==t['candidates'])
 check('deterministic candidate permutation',r.candidates(t,'B_winner_top8',1)==r.candidates(t,'B_winner_top8',1))
 check('winner scores top eight',len(r.choose(t,r.candidates(t,'B_winner_top8',1),'B_winner_top8',design,stub_rank)[0])==8)
 check('shortlist selected four',len(r.choose(t,r.candidates(t,'C_shortlist_default',1),'C_shortlist_default',design,stub_rank)[0])==4)
 for arm,rep in [('A_no_rank',0),('B_winner_top8',1),('C_shortlist_default',1),('D_shortlist_tuned',1)]:
  row=r.artifact(t,arm,rep,design,execution,stub_rank,stub_main)
  check('artifact '+arm,row['arm_id']==arm and row['models']['main']==execution['main']['model'] and row['usage']['main_input_tokens']==500)
 check('MAIN CLI response parser accepts captured envelope',r.parse_main_response(json.loads((ROOT/'main-cli-contract.fixture.json').read_text()),execution)[2]==execution['main']['model'])
 malformed=json.loads((ROOT/'main-cli-contract.fixture.json').read_text());malformed['data'].pop('usage')
 try:r.parse_main_response(malformed,execution);raise AssertionError('missing usage accepted')
 except RuntimeError as e:check('MAIN missing usage fails closed',str(e)=='main_usage_missing_or_invalid')
 check('schedule exactly 160 with local custody bundle',len(r.schedule())==160 if r.gate.RUNNER_INPUTS.exists() else len(r.schedule())==0)
 with tempfile.TemporaryDirectory() as td:
  saved=r.preflight; saved_inputs=r.gate.RUNNER_INPUTS
  synthetic=Path(td)/'runner-inputs';synthetic.mkdir()
  for i in range(1,17):
   x=task();x['task_id']=f'p2-score-en-{i:02d}'
   (synthetic/f"{x['task_id']}.json").write_text(json.dumps(x),encoding='utf-8')
  r.gate.RUNNER_INPUTS=synthetic
  saved_lock=r.gate.INPUT_LOCK;r.gate.INPUT_LOCK=Path(td)/'inputs.lock.json';r.gate.INPUT_LOCK.write_text('{}')
  r.preflight=lambda: {'test_lock':True}
  out=Path(td)/'outputs'
  try:
   with contextlib.redirect_stdout(io.StringIO()):
    result=r.execute(out,rank_fn=lambda obj: (_ for _ in ()).throw(RuntimeError('stub_failure')),main_fn=stub_main)
   check('failed calls still produce all 160 artifacts',result['outputs']==160)
   check('exactly 160 output JSON files',len(list(out.glob('*.json')))==160)
   failed=json.loads((out/'p2-score-en-01__B_winner_top8__rep1.json').read_text())
   check('failure is explicit abstention',failed['selection']['status']=='failed' and failed['answer']=='')
   check('unknown billed usage is null, not zero',failed['usage']['jev_input_tokens'] is None and failed['usage']['main_input_tokens'] is None)
  finally:r.preflight=saved;r.gate.RUNNER_INPUTS=saved_inputs;r.gate.INPUT_LOCK=saved_lock
 with tempfile.TemporaryDirectory() as td:
  saved=r.gate.INPUT_LOCK;r.gate.INPUT_LOCK=Path(td)/'nonexistent.json'
  try:
   try:r.preflight();raise AssertionError('missing lock was accepted')
   except RuntimeError as e:check('missing lock fail closed',str(e)=='missing_input_lock')
  finally:r.gate.INPUT_LOCK=saved
 print(json.dumps({'ok':True,'tests':len(checks),'names':checks}));return 0
if __name__=='__main__':sys.exit(main())
