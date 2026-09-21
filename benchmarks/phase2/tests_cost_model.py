#!/usr/bin/env python3
"""Offline checks of the approved Phase 2 modeled-price gate."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
import cost_model as m

def main():
    prices=json.loads((ROOT/'config/execution.json').read_text())['pricing'];checks=[]
    def check(name,condition):
        assert condition,name;checks.append(name)
    a={'jev_input_tokens':0,'jev_output_tokens':0,'main_input_tokens':2000,'main_output_tokens':100,'main_cache_read_input_tokens':0,'main_cache_creation_input_tokens':0}
    c={'jev_input_tokens':1000,'jev_output_tokens':20,'main_input_tokens':1000,'main_output_tokens':100,'main_cache_read_input_tokens':0,'main_cache_creation_input_tokens':0}
    check('actual tokens with public rates',m.modeled_run(a,prices,'A_no_rank')>m.modeled_run(c,prices,'C_shortlist_default'))
    rows=[]
    for i in range(16):
        for arm,reps,u in [('A_no_rank',1,a),('C_shortlist_default',3,c)]:
            rows.extend({'task_id':f't{i:02}', 'arm_id':arm,'selection':{'status':'completed'},'usage':u,'accounting_status':'complete','accounting_attempts':[{'status':'accepted','usage_complete':True}]} for _ in range(reps))
    result=m.paired_gate(rows,prices)
    check('paired positive modeled gate',result['decision']=='PASS')
    check('mean and A/C ratio reported',float(result['modeled_mean_savings_usd_per_task'])>0 and 0<float(result['modeled_cost_ratio_shortlist_to_baseline'])<1)
    for name,bad in [('missing token',dict(c,main_output_tokens=None)),('missing cache bucket',dict(c,main_cache_read_input_tokens=None)),('cache write without frozen rate',dict(c,main_cache_creation_input_tokens=1))]:
        try:m.modeled_run(bad,prices,'C_shortlist_default');raise AssertionError(name+' accepted')
        except m.CostUnknown:checks.append(name+' rejected')
    rows[-1]=dict(rows[-1],accounting_status='unknown')
    try:m.paired_gate(rows,prices);raise AssertionError('unknown attempt accepted')
    except m.CostUnknown:checks.append('unknown attempt inconclusive')
    check('historical input lock unchanged',(__import__('hashlib').sha256((ROOT/'inputs.lock.json').read_bytes()).hexdigest()=='e2b9769aa2aab9859eee40a2744c8688ed9b92fa899346bc45a5cdf6424fbb0e') if (ROOT/'inputs.lock.json').exists() else True)
    print(json.dumps({'ok':True,'tests':len(checks),'checks':checks}));return 0
if __name__=='__main__':sys.exit(main())
