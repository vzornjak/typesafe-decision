#!/usr/bin/env python3
"""Verify full input custody outside, scoped bytes inside, without excluded files."""
import hashlib,json
from pathlib import Path

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def attest(full,scoped,original_lock,commit):
 full=Path(full);scoped=Path(scoped);lock=json.loads(Path(original_lock).read_text());rows=lock['files'];verified=[];excluded=[]
 if len(rows)!=91 or len({r['path'] for r in rows})!=91:raise ValueError('unexpected_or_duplicate_input_rows')
 if not all((full/'benchmarks/phase2'/r['path']).is_file() and sha(full/'benchmarks/phase2'/r['path'])==r['sha256'] and (full/'benchmarks/phase2'/r['path']).stat().st_size==r['bytes'] for r in rows):raise ValueError('full_input_lock_mismatch')
 if hashlib.sha256(canonical(rows)).hexdigest()!=lock['aggregate_sha256']:raise ValueError('full_input_aggregate_mismatch')
 for r in rows:
  p=scoped/'benchmarks/phase2'/r['path']
  if p.exists():verified.append(r['path'])
  else:excluded.append(r['path'])
 if 'DEVIATIONS.md' not in excluded:raise ValueError('deviation_must_be_excluded')
 if not any(p.startswith('runner-inputs/p2-score-') for p in verified):raise ValueError('missing_runner_inputs')
 report={'schema_version':1,'kind':'scoped_phase2_input_attestation','historical_lock_sha256':sha(original_lock),
         'historical_aggregate_sha256':lock['aggregate_sha256'],'historical_commit':lock['git_commit'],
         'runner_commit':commit,'full_91_verified_outside':len(rows)==91,'enforce_scored_inputs':True,'included':sorted(verified),'excluded':sorted(excluded)}
 if not report['full_91_verified_outside']:raise ValueError('unexpected_input_count')
 return report

def verify(scoped,attestation,lock_path,commit):
 scoped=Path(scoped);report=json.loads(Path(attestation).read_text());lock=json.loads(Path(lock_path).read_text())
 if report.get('kind')!='scoped_phase2_input_attestation' or not report.get('full_91_verified_outside'):raise ValueError('invalid_attestation')
 if report['historical_lock_sha256']!=sha(lock_path) or report['historical_aggregate_sha256']!=lock['aggregate_sha256'] or report['runner_commit']!=commit:raise ValueError('attestation_lock_or_commit_mismatch')
 rows={r['path']:r for r in lock['files']}; included=set(report['included']); excluded=set(report['excluded'])
 if len(lock.get('files',[]))!=91 or len(rows)!=91:raise ValueError('input_lock_row_count_mismatch')
 if hashlib.sha256(canonical(lock['files'])).hexdigest()!=lock['aggregate_sha256']:raise ValueError('historical_manifest_corrupt')
 if included&excluded or included|excluded!=set(rows):raise ValueError('incomplete_scope_partition')
 if 'DEVIATIONS.md' not in excluded:raise ValueError('gold_derived_deviation_exposed')
 if report.get('enforce_scored_inputs'):
  expected_inputs={f'runner-inputs/p2-score-{lang}-{i:02d}.json' for lang in ('hr','en') for i in range(1,9)}|{'runner-inputs/MANIFEST.json','PREREGISTRATION.md','config/design.json','config/execution.json','config/decision-gates.json','config/metadata-policy.json','prompts/main-system.md','prompts/main-user-template.md'}
  if not expected_inputs<=included:raise ValueError('required_scoped_inputs_missing')
 for name,r in rows.items():
  p=scoped/'benchmarks/phase2'/name
  if name in excluded:
   if p.exists():raise ValueError('excluded_path_present:'+name)
  elif not p.is_file() or sha(p)!=r['sha256'] or p.stat().st_size!=r['bytes']:
   raise ValueError('included_file_mismatch:'+name)
 if any(p.is_file() for p in scoped.rglob('*') if any(x in str(p.relative_to(scoped)).lower() for x in ('sealed-gold','deviations.md','curation.md','private-development'))):raise ValueError('forbidden_runner_file')
 return {'ok':True,'verified_included':len(included),'excluded':len(excluded),'input_lock_sha256':sha(lock_path)}
