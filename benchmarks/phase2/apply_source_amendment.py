#!/usr/bin/env python3
"""Apply ten transport-confirmed source replacements without using gold."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent; PROV=ROOT/"builder-provenance"
REPL={
 ("p2-score-en-03","c09"):("https://digital-strategy.ec.europa.eu/en/policies/ai-act","open-reuse","browser-confirmed 404; use official AI Act topic page as partial-overlap candidate"),
 ("p2-score-en-06","c10"):("https://www.nhlbi.nih.gov/health/high-blood-pressure/treatment","public-domain","browser-confirmed FDA 404; use adjacent NHLBI treatment/lifestyle context"),
 ("p2-score-en-08","c08"):("https://www.ftc.gov/business-guidance/resources/shopping-home-appliances-use-energyguide-label","public-domain","FTC rule index blocked; replace with official EnergyGuide consumer/business explanation"),
 ("p2-score-hr-03","c06"):("https://transport.ec.europa.eu/transport-themes/passenger-rights_en","open-reuse","browser-confirmed 404; use official general passenger-rights overview as partial candidate"),
 ("p2-score-hr-03","c08"):("https://transport.ec.europa.eu/transport-themes/passenger-rights/air-passenger-rights_en","open-reuse","browser-confirmed 404; use current official air-passenger-rights overview"),
 ("p2-score-hr-04","c02"):("https://www.edpb.europa.eu/sme-data-protection-guide/respect-individuals-rights/data-protection-impact-assessment_en","link-or-short-excerpt-only","old EDPB guideline route soft-errors; use current EDPB SME DPIA guide"),
 ("p2-score-hr-04","c04"):("https://www.edpb.europa.eu/sme-data-protection-guide/data-breaches_en","link-or-short-excerpt-only","old examples guideline route soft-errors; reuse current live breach guide as intentional near-duplicate"),
 ("p2-score-hr-05","c09"):("https://www.who.int/europe/news-room/fact-sheets/item/heat-and-health","open-reuse","WHO publication permalink 404; use WHO Europe fact sheet"),
 ("p2-score-hr-08","c09"):("https://energy-efficient-products.ec.europa.eu/product-list/local-space-heaters_en","open-reuse","old boilers slug 404; use related official heater category as partial candidate"),
 ("p2-score-hr-08","c10"):("https://www.energystar.gov/products/heat_pumps","public-domain","old EC heat-pumps slug 404; use official ENERGY STAR heat-pump overview"),
}
def main():
 log=[]
 for (tid,cid),(url,reuse,reason) in REPL.items():
  p=PROV/f"{tid}.sources.json"; x=json.load(open(p)); row=next(c for c in x['candidates'] if c['candidate_id']==cid)
  old=row['url']; row.update({'url':url,'reuse_class':reuse,'replaces_url':old,'replacement_reason':reason})
  p.write_text(json.dumps(x,indent=2)+'\n'); log.append({'task_id':tid,'candidate_id':cid,'old_url':old,'new_url':url,'reuse_class':reuse,'reason':reason})
 (PROV/'source-plan-amendment-01.json').write_text(json.dumps({'kind':'source_plan_amendment','gold_visible':False,'changes':log},indent=2)+'\n')
 print(json.dumps({'ok':True,'changes':len(log)}))
if __name__=='__main__':main()
