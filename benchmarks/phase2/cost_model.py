#!/usr/bin/env python3
"""Phase 2 A-001 modeled public-list-price cost gate; no scored gold access."""
from decimal import Decimal

MILLION=Decimal(1_000_000)
class CostUnknown(ValueError): pass

def nonnegative_int(value,name):
    if type(value) is not int or value<0:raise CostUnknown('unknown_or_invalid_'+name)
    return value

def modeled_run(usage,prices,arm,cache_semantics='separate_additive'):
    """Return modeled USD from provider-reported tokens only.

    Cache semantics are frozen as separate_additive for Anthropic-style usage:
    input_tokens excludes cache_creation_input_tokens and cache_read_input_tokens.
    No cache write rate was preregistered, so any nonzero cache writes abstain.
    """
    if cache_semantics!='separate_additive':raise CostUnknown('cache_semantics_unregistered')
    required=('jev_input_tokens','jev_output_tokens','main_input_tokens','main_output_tokens')
    if not isinstance(usage,dict):raise CostUnknown('usage_not_object')
    u={key:nonnegative_int(usage.get(key),key) for key in required}
    read=nonnegative_int(usage.get('main_cache_read_input_tokens',0),'main_cache_read_input_tokens')
    write=nonnegative_int(usage.get('main_cache_creation_input_tokens',0),'main_cache_creation_input_tokens')
    if write:raise CostUnknown('cache_write_price_not_frozen')
    if arm=='A_no_rank' and (u['jev_input_tokens'] or u['jev_output_tokens']):raise CostUnknown('baseline_jev_usage_nonzero')
    def rate(key):
        x=prices.get(key)
        if type(x) not in (int,float) or x<0:raise CostUnknown('missing_price_'+key)
        return Decimal(str(x))
    cost=(Decimal(u['jev_input_tokens'])*rate('jev_input_per_million')+
          Decimal(u['jev_output_tokens'])*rate('jev_output_per_million')+
          Decimal(u['main_input_tokens'])*rate('main_input_per_million')+
          Decimal(read)*rate('main_cached_input_per_million')+
          Decimal(u['main_output_tokens'])*rate('main_output_per_million'))/MILLION
    return cost

def paired_gate(rows,prices):
    """Rows are task-level already-accounted A/C usages; repetitions nested in task."""
    tasks={}
    for row in rows:
        if not isinstance(row,dict):raise CostUnknown('invalid_row')
        task=row.get('task_id');arm=row.get('arm_id')
        if arm not in ('A_no_rank','C_shortlist_default') or not isinstance(task,str):continue
        if row.get('selection',{}).get('status')!='completed':raise CostUnknown('incomplete_run')
        if row.get('accounting_status','complete')!='complete':raise CostUnknown('unreconciled_attempts')
        tasks.setdefault(task,{}).setdefault(arm,[]).append(modeled_run(row.get('usage'),prices,arm))
    if len(tasks)!=16:raise CostUnknown('expected_16_tasks')
    diffs=[]
    for task,arms in sorted(tasks.items()):
        if len(arms.get('A_no_rank',[]))!=1 or len(arms.get('C_shortlist_default',[]))!=3:
            raise CostUnknown('missing_or_duplicate_arm_runs_'+task)
        a=arms['A_no_rank'][0];c=sum(arms['C_shortlist_default'])/3
        diffs.append(a-c)
    total=sum(diffs)
    return {'decision':'PASS' if total>0 else 'FAIL','unit':'modeled_public_list_price_usd',
            'task_count':16,'modeled_total_savings_usd':str(total),
            'task_savings_usd':[str(x) for x in diffs],
            'actual_account_charge':'unknown_not_measured'}
