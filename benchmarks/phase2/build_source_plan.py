#!/usr/bin/env python3
"""Build the audited final URL/reuse plan. No gold labels are used."""
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parent
PUB=ROOT/"public"
AUDIT=ROOT/"builder-provenance"/"source-audit-technical-policy.md"

OPAQUE_TO_TASK={
 "r5dw-8kqa":"p2-score-hr-01","x1pn-4hju":"p2-score-hr-02","m9gt-2cwf":"p2-score-en-01","c6vy-7lne":"p2-score-en-02",
 "h3qs-9btk":"p2-score-hr-03","a8lr-5xpd":"p2-score-hr-04","u2fm-6jrc":"p2-score-en-03","k7nb-1zmh":"p2-score-en-04",
}

def parse_audit():
 text=AUDIT.read_text(encoding="utf-8"); out={}
 for opaque,tid in OPAQUE_TO_TASK.items():
  block=text.split(f"## `{opaque}`",1)[1]
  block=block.split("\n## `",1)[0]
  rows=[]
  for line in block.splitlines():
   cols=[x.strip() for x in line.strip().strip('|').split('|')]
   if len(cols)>=10 and cols[0].startswith('https://') and cols[8]=='keep':
    rows.append({"url":cols[0],"reuse_class":cols[6]})
  if len(rows)!=10: raise ValueError(f"{opaque}: {len(rows)} kept rows")
  out[tid]=rows
 return out

MANUAL={
 "p2-score-hr-05":[
  ("https://www.who.int/news-room/fact-sheets/detail/climate-change-heat-and-health","open-reuse"),("https://www.who.int/europe/health-topics/heatwaves","open-reuse"),("https://www.who.int/europe/publications/i/item/9789289071918","open-reuse"),("https://climate-adapt.eea.europa.eu/en/observatory/evidence/health-effects/heat-and-health","open-reuse"),("https://www.weather.gov/safety/heat","public-domain"),("https://www.weather.gov/safety/heat-illness","public-domain"),("https://www.ready.gov/heat","public-domain"),("https://meteo.hr/prognoze.php?section=prognoze_specp&param=toplinski_val","unknown"),("https://www.who.int/publications/i/item/9789240091913","open-reuse"),("https://www.who.int/europe/publications/i/item/9789289055406","open-reuse")],
 "p2-score-hr-06":[
  ("https://www.who.int/news-room/fact-sheets/detail/cervical-cancer","open-reuse"),("https://www.who.int/teams/immunization-vaccines-and-biologicals/diseases/human-papillomavirus-vaccines-(HPV)","open-reuse"),("https://www.who.int/publications/i/item/who-wer9750-645-672","open-reuse"),("https://www.hzjz.hr/aktualnosti/cijepljenje-protiv-humanog-papiloma-virusa-hpv/","link-or-short-excerpt-only"),("https://www.nhs.uk/vaccinations/hpv-vaccine/","open-reuse"),("https://www.nhs.uk/tests-and-treatments/cervical-screening/","open-reuse"),("https://www.cancer.gov/about-cancer/causes-prevention/risk/infectious-agents/hpv-vaccine-fact-sheet","public-domain"),("https://www.cancer.gov/types/cervical/screening","public-domain"),("https://www.ema.europa.eu/en/medicines/human/EPAR/gardasil-9","open-reuse"),("https://www.ema.europa.eu/en/human-regulatory-overview/public-health-threats/human-papillomavirus-hpv-vaccines","open-reuse")],
 "p2-score-en-05":[
  ("https://www.epa.gov/indoor-air-quality-iaq/ventilation-and-respiratory-viruses","public-domain"),("https://www.epa.gov/indoor-air-quality-iaq/air-cleaners-and-air-filters-home","public-domain"),("https://www.epa.gov/iaq-schools","public-domain"),("https://www.epa.gov/iaq-schools/framework-effective-school-iaq-management","public-domain"),("https://www.who.int/publications/i/item/9789240021280","open-reuse"),("https://www.ashrae.org/technical-resources/filtration-disinfection","link-or-short-excerpt-only"),("https://www.hse.gov.uk/ventilation/index.htm","open-reuse"),("https://www.hse.gov.uk/ventilation/assessing-the-risk-of-poor-ventilation.htm","open-reuse"),("https://www.hse.gov.uk/ventilation/how-to-improve-ventilation.htm","open-reuse"),("https://www.hse.gov.uk/ventilation/examples-of-improving-ventilation.htm","open-reuse")],
 "p2-score-en-06":[
  ("https://www.nhlbi.nih.gov/health/high-blood-pressure","public-domain"),("https://www.nhlbi.nih.gov/health/high-blood-pressure/diagnosis","public-domain"),("https://www.uspreventiveservicestaskforce.org/uspstf/recommendation/hypertension-in-adults-screening","public-domain"),("https://www.who.int/news-room/fact-sheets/detail/hypertension","open-reuse"),("https://www.nice.org.uk/guidance/ng136","open-reuse"),("https://www.nice.org.uk/guidance/ng136/chapter/recommendations","open-reuse"),("https://www.nhs.uk/tests-and-treatments/blood-pressure-test/","open-reuse"),("https://www.validatebp.org/","link-or-short-excerpt-only"),("https://stridebp.org/","link-or-short-excerpt-only"),("https://www.fda.gov/medical-devices/vitro-diagnostics/blood-pressure-monitoring-devices","public-domain")],
 "p2-score-hr-07":[
  ("https://www.fueleconomy.gov/feg/Find.do?action=sbsSelect","public-domain"),("https://www.fueleconomy.gov/feg/evtech.shtml","public-domain"),("https://www.fueleconomy.gov/feg/label/learn-more-electric-label.shtml","public-domain"),("https://afdc.energy.gov/fuels/electricity.html","public-domain"),("https://afdc.energy.gov/calc/","public-domain"),("https://afdc.energy.gov/stations/","public-domain"),("https://www.epa.gov/greenvehicles/electric-vehicle-myths","public-domain"),("https://alternative-fuels-observatory.ec.europa.eu/","open-reuse"),("https://transport.ec.europa.eu/transport-themes/clean-transport/alternative-fuels-sustainable-mobility-europe_en","open-reuse"),("https://eur-lex.europa.eu/eli/reg/2023/1804/oj","open-reuse")],
 "p2-score-hr-08":[
  ("https://energy-efficient-products.ec.europa.eu/product-list/space-heaters_en","open-reuse"),("https://eprel.ec.europa.eu/screen/product/spaceheaters","open-reuse"),("https://eur-lex.europa.eu/eli/reg_del/2013/811/oj","open-reuse"),("https://eur-lex.europa.eu/eli/reg/2013/813/oj","open-reuse"),("https://www.energystar.gov/products/air_source_heat_pumps","public-domain"),("https://www.energy.gov/cmei/femp/purchasing-energy-efficient-residential-air-source-heat-pumps","public-domain"),("https://www.iea.org/reports/the-future-of-heat-pumps/how-a-heat-pump-works","link-or-short-excerpt-only"),("https://www.gov.uk/government/publications/heat-pump-net-zero-investment-roadmap","open-reuse"),("https://energy-efficient-products.ec.europa.eu/product-list/boilers_en","open-reuse"),("https://energy-efficient-products.ec.europa.eu/product-list/heat-pumps_en","open-reuse")],
 "p2-score-en-07":[
  ("https://www.cisa.gov/news-events/news/securing-wireless-networks","public-domain"),("https://www.cisa.gov/news-events/news/home-network-security","public-domain"),("https://consumer.ftc.gov/articles/how-secure-your-home-wi-fi-network","public-domain"),("https://pages.nist.gov/IoT-Device-Cybersecurity-Requirement-Catalogs/","public-domain"),("https://www.nist.gov/itl/applied-cybersecurity/nist-cybersecurity-iot-program","public-domain"),("https://www.nist.gov/publications/foundational-cybersecurity-activities-iot-device-manufacturers","public-domain"),("https://www.nist.gov/publications/iot-device-cybersecurity-guidance-federal-government-establishing-iot-device","public-domain"),("https://www.ncsc.gov.uk/collection/device-security-guidance","open-reuse"),("https://www.gov.uk/government/publications/the-uk-product-security-and-telecommunications-infrastructure-product-security-regime","open-reuse"),("https://www.gov.uk/government/publications/code-of-practice-for-consumer-iot-security","open-reuse")],
 "p2-score-en-08":[
  ("https://energy-efficient-products.ec.europa.eu/product-list/washing-machines_en","open-reuse"),("https://eprel.ec.europa.eu/screen/product/washingmachines2019","open-reuse"),("https://eur-lex.europa.eu/eli/reg_del/2019/2014/oj","open-reuse"),("https://eur-lex.europa.eu/eli/reg/2019/2023/oj","open-reuse"),("https://www.energystar.gov/products/clothes_washers","public-domain"),("https://www.energystar.gov/products/clothes_washers/key_product_criteria","public-domain"),("https://www.energy.gov/eere/buildings/appliance-and-equipment-standards-program","public-domain"),("https://www.ftc.gov/legal-library/browse/rules/energy-labeling-rule","public-domain"),("https://www.ecfr.gov/current/title-16/chapter-I/subchapter-D/part-305","public-domain"),("https://www.ecfr.gov/current/title-10/chapter-II/subchapter-D/part-430","public-domain")],
}

def main():
 plan=parse_audit()
 for tid,rows in MANUAL.items(): plan[tid]=[{"url":u,"reuse_class":r} for u,r in rows]
 if len(plan)!=16 or any(len(v)!=10 for v in plan.values()): raise SystemExit("plan must be 16x10")
 for tid,rows in sorted(plan.items()):
  task=json.load(open(PUB/f"{tid}.json",encoding="utf-8"))
  for i,(candidate,row) in enumerate(zip(task["candidates"],rows),1):
   candidate["url"]=row["url"]; candidate["domain"]=re.sub(r'^www\.','',row["url"].split('/')[2].lower())
  (PUB/f"{tid}.json").write_text(json.dumps(task,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
  (ROOT/"builder-provenance"/f"{tid}.sources.json").write_text(json.dumps({"task_id":tid,"candidates":[dict(candidate_id=f"c{i:02d}",**row) for i,row in enumerate(rows,1)]},indent=2)+"\n")
 print(json.dumps({"ok":True,"tasks":len(plan),"sources":sum(map(len,plan.values()))}))
if __name__=="__main__": main()
