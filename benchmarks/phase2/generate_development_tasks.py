#!/usr/bin/env python3
"""Generate four synthetic Phase 2 development tasks. Never generates scored tasks or gold."""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent / "public"

SPECS = [
    {
        "task_id": "p2-dev-hr-01", "language": "hr", "domain": "software_technical", "complexity": "moderate",
        "query": "Usporedi dva dokumentirana načina uvođenja cachea u web API te preporuči kada koristiti svaki pristup, uključujući invalidaciju i opažljivost.",
        "requirements": [
            ("r01", "Objasniti cache-aside pristup i njegove kompromise"),
            ("r02", "Objasniti write-through pristup i njegove kompromise"),
            ("r03", "Usporediti invalidaciju i opažljivost oba pristupa"),
        ],
        "topics": [
            ("Cache-aside obrazac", "Aplikacija prvo provjerava cache, zatim čita bazu pri promašaju i sprema rezultat. Prednosti su jednostavno postupno uvođenje i kontrola u aplikaciji. Rizici su zastarjeli zapisi, stampede pri isteku i složenija invalidacija."),
            ("Write-through obrazac", "Svaki zapis prolazi kroz cache i trajnu pohranu prije potvrde. Čitanja su češće zagrijana i konzistencija je predvidljivija, ali zapis ima veću latenciju i cache može sadržavati rijetko korištene podatke."),
            ("Invalidacija", "TTL ograničava starost, eksplicitna invalidacija reagira na promjene, a verzionirani ključevi olakšavaju atomsku zamjenu. Potrebno je definirati ponašanje pri padu cachea."),
            ("Opažljivost cachea", "Mjeri hit rate, miss rate, evictione, latenciju, stampede događaje i razliku između cache i izvornog sustava. Alarm samo na hit rate bez konteksta prometa može zavarati."),
        ],
    },
    {
        "task_id": "p2-dev-hr-02", "language": "hr", "domain": "public_policy_regulation", "complexity": "complex",
        "query": "Pripremi pregled kako bi mali grad trebao uvesti program otvorenih podataka: pravna osnova, privatnost, licenciranje, kvaliteta, verzioniranje i mjerenje učinka.",
        "requirements": [
            ("r01", "Opisati pravnu i upravljačku osnovu programa"),
            ("r02", "Objasniti zaštitu privatnosti prije objave"),
            ("r03", "Predložiti otvoreno licenciranje i uvjete ponovne uporabe"),
            ("r04", "Definirati kvalitetu, metapodatke i verzioniranje skupova"),
            ("r05", "Predložiti mjerljive pokazatelje učinka programa"),
        ],
        "topics": [
            ("Upravljanje otvorenim podacima", "Grad treba imenovati vlasnike skupova, katalog, raspored objave i postupak ispravaka. Odluka treba razlikovati zakonsku obvezu objave od dobrovoljne transparentnosti."),
            ("Procjena privatnosti", "Prije objave treba ukloniti izravne identifikatore, procijeniti mogućnost povezivanja zapisa i dokumentirati rizik ponovne identifikacije. Agregiranje i pragovi malih ćelija smanjuju rizik."),
            ("Otvorena licenca", "Jasna standardna licenca treba dopustiti ponovnu uporabu uz uvjete atribucije. Posebna ograničenja po skupu otežavaju automatiziranu uporabu i trebaju biti iznimka."),
            ("Kvaliteta i verzije", "Katalog treba navesti shemu, jedinice, vremenski obuhvat, učestalost ažuriranja, kontakt i poznata ograničenja. Stabilne verzije i changelog omogućuju reproducibilnu uporabu."),
            ("Mjerenje učinka", "Broj preuzimanja nije dovoljan. Prati dostupnost, svježinu, greške, broj korisnih ponovnih uporaba, vrijeme odgovora na prijave i primjere javne koristi."),
        ],
    },
    {
        "task_id": "p2-dev-en-01", "language": "en", "domain": "science_health", "complexity": "moderate",
        "query": "Explain how to compare two home air-quality interventions for particulate matter, including evidence quality, measurement design, and important limitations.",
        "requirements": [
            ("r01", "Compare filtration and source-control interventions"),
            ("r02", "Describe a credible particulate-matter measurement design"),
            ("r03", "Explain evidence-quality and interpretation limitations"),
        ],
        "topics": [
            ("Portable filtration", "A correctly sized particle filter can reduce indoor particulate concentrations while operating. Performance depends on clean-air delivery rate, room volume, placement, fan setting, filter loading, and outdoor infiltration."),
            ("Source control", "Removing indoor emission sources and reducing particle entry can prevent pollution rather than treating it after release. Effects vary with cooking, smoking, ventilation behavior, building leakage, and outdoor conditions."),
            ("Measurement design", "Use calibrated sensors in comparable locations, establish a baseline, record intervention periods, and track outdoor particulate matter, occupancy, ventilation, and episodic sources. Repeated measurements are stronger than one before-after reading."),
            ("Evidence limits", "Sensor error, temporal confounding, room differences, adherence, and short follow-up can exaggerate an apparent effect. Lower particle concentration is an intermediate outcome and does not by itself prove a health benefit."),
        ],
    },
    {
        "task_id": "p2-dev-en-02", "language": "en", "domain": "consumer_product", "complexity": "complex",
        "query": "Create a decision guide for choosing between a repairable laptop and a thin sealed laptop, covering performance, battery, repairability, lifetime cost, software support, and environmental tradeoffs.",
        "requirements": [
            ("r01", "Compare sustained performance and portability"),
            ("r02", "Compare battery capacity, efficiency, and replacement"),
            ("r03", "Assess repairability and upgrade paths"),
            ("r04", "Compare lifetime cost and software-support horizon"),
            ("r05", "Discuss environmental tradeoffs without simplistic claims"),
        ],
        "topics": [
            ("Performance and form factor", "Thin systems can optimize weight and short burst performance, while larger modular systems may sustain loads with more cooling. Actual results depend on processor class, thermal limits, workload, and power profile."),
            ("Battery tradeoffs", "Battery life combines capacity, component efficiency, display use, workload, and software. A replaceable pack may extend service life, but replacement availability and safe procedures matter more than the label alone."),
            ("Repair and upgrades", "Socketed or accessible storage, memory, ports, keyboard, and battery can reduce repair scope. Parts pricing, manuals, diagnostic tools, warranty terms, and long-term availability determine practical repairability."),
            ("Lifetime cost and support", "Purchase price should be combined with likely repairs, upgrades, downtime, resale value, and the operating-system support horizon. A cheap repairable device is not economical if critical parts disappear early."),
            ("Environmental interpretation", "Longer useful life can spread manufacturing impact over more years, but heavier materials, inefficient operation, unused upgrades, shipping parts, and recycling pathways also matter. Compare a defined usage period rather than slogans."),
        ],
    },
]

DISTRACTORS = [
    ("Unrelated announcement", "This synthetic notice announces a community event and contains no evidence relevant to the research requirements. It exists to test rejection of superficially polished but irrelevant material."),
    ("Marketing overview", "This synthetic promotional page uses broad claims such as best, effortless, and revolutionary without methods, measurements, boundaries, or evidence. It should not dominate documented technical tradeoffs."),
    ("Outdated summary", "This synthetic summary omits dates, versions, methods, and limitations. It may mention the general topic but cannot support a detailed current comparison or recommendation."),
    ("Forum anecdote", "One anonymous synthetic user reports a personal experience without a baseline, control, reproducible setup, or independent verification. The anecdote may suggest a question but cannot establish a general conclusion."),
    ("Terminology glossary", "This synthetic glossary defines a few broad terms but provides no comparative evidence, implementation details, measurements, costs, or limitations required by the query."),
    ("Duplicate digest", "This synthetic digest repeats fragments from a stronger candidate while removing qualifications and provenance. It tests whether near-duplicate low-information material consumes selection budget."),
]


def make(spec):
    candidates = []
    content_rows = spec["topics"] + DISTRACTORS
    for i, (title, content) in enumerate(content_rows, 1):
        # Add enough neutral context for realistic chunk size without introducing hidden labels.
        full = content + " The document is synthetic and was authored only for development-set harness testing; it is not scored benchmark evidence."
        candidates.append({
            "candidate_id": f"c{i:02d}", "url": f"https://phase2-dev-{spec['task_id']}-{i}.test/document",
            "title": title, "domain": f"phase2-dev-{i}.test", "published_at_if_observable": None,
            "content": full, "content_chars": len(full),
        })
    return {k: spec[k] for k in ("task_id", "language", "domain", "complexity", "query")} | {
        "requirements": [{"id": i, "text": t} for i, t in spec["requirements"]], "candidates": candidates,
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for spec in SPECS:
        p = OUT / f"{spec['task_id']}.json"
        p.write_text(json.dumps(make(spec), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "tasks": len(SPECS), "origin": "synthetic_development_only"}))


if __name__ == "__main__": main()
