#!/usr/bin/env python3
"""Offline scoped attestation tests against small synthetic fixtures."""
import hashlib,json,tempfile,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
import scoped_inputs as m

def main():
 checks=[]
 def check(label,value):
  assert value,label;checks.append(label)
 with tempfile.TemporaryDirectory() as td:
  base=Path(td);full=base/'full';subset=base/'subset'
  for d in (full,subset):(d/'benchmarks/phase2').mkdir(parents=True)
  names=['DEVIATIONS.md','runner-inputs/p2-score-hr-01.json']
  rows=[]
  for name in names:
   p=full/'benchmarks/phase2'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(name)
   rows.append({'path':name,'bytes':len(p.read_bytes()),'sha256':m.sha(p)})
  p=subset/'benchmarks/phase2'/names[1];p.parent.mkdir(parents=True,exist_ok=True);p.write_text(names[1])
  # Use a full 91-entry synthetic lock; all other entries remain excluded.
  for i in range(89):
   name=f'config/dummy{i:02d}.json';p=full/'benchmarks/phase2'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(name)
   rows.append({'path':name,'bytes':len(p.read_bytes()),'sha256':m.sha(p)})
  lock=base/'input.json';lock.write_text(json.dumps({'files':rows,'aggregate_sha256':hashlib.sha256(m.canonical(rows)).hexdigest(),'git_commit':'synthetic'}))
  report=m.attest(full,subset,lock,'runner-commit');report['enforce_scored_inputs']=False;a=subset/'CUSTODY-MANIFEST.json';a.write_text(json.dumps(report))
  check('all 91 attested externally',len(report['included'])+len(report['excluded'])==91)
  check('scoped bytes pass',m.verify(subset,a,lock,'runner-commit')['verified_included']==1)
  target=subset/'benchmarks/phase2'/names[1];target.write_text('tampered')
  try:m.verify(subset,a,lock,'runner-commit');raise AssertionError('tamper accepted')
  except ValueError:check('tamper rejected',True)
  target.write_text(names[1]);q=subset/'benchmarks/phase2/DEVIATIONS.md';q.write_text('forbidden')
  try:m.verify(subset,a,lock,'runner-commit');raise AssertionError('excluded file accepted')
  except ValueError:check('excluded file rejected',True)
 print(json.dumps({'ok':True,'tests':len(checks),'checks':checks}));return 0
if __name__=='__main__':sys.exit(main())
