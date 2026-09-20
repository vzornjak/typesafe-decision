# Phase 2 — prijedlog javnog dvojezičnog skupa zadataka

## Kontrole dizajna

- **Razvojni skup:** 4 zadatka, po jedan iz svake domene; nije dio scored metrike.
- **Scored skup:** 16 zadataka.
- **Jezik scored skupa:** točno **8 HR / 8 EN**.
- **Domene scored skupa:** točno **4 zadatka po domeni**.
- **Složenost scored skupa:** točno **8 moderate** s 2–3 zahtjeva i **8 complex** s 4–6 zahtjeva.
- Svaki zadatak ima **10 kandidatskih URL-ova**.
- Zahtjevi su izvedeni samo iz korisničkog upita i ne spominju dokumente, izvore, očekivane citate ni gold.
- Nema `required`, `primary`, `support`, authority ili sličnih evaluacijskih oznaka.
- Kandidati su javno dostupni i ne traže privatne podatke, prijavu ili pretplatu.
- Upiti i liste kandidata novo su sastavljeni za Phase 2; nisu preuzeti iz starog TypeSafe benchmarka. Prije zaključavanja preporučuje se mehanička provjera normaliziranih URL-ova i query-hasheva protiv zasebne exclusion liste starog korpusa, bez otvaranja njegova gold sadržaja.

## Matrica scored skupa

| Domena | HR moderate | HR complex | EN moderate | EN complex |
|---|---:|---:|---:|---:|
| Software / technical documentation | 1 | 1 | 1 | 1 |
| Public policy / regulation | 1 | 1 | 1 | 1 |
| Science / health evidence | 1 | 1 | 1 | 1 |
| Consumer / product comparison | 1 | 1 | 1 | 1 |
| **Ukupno** | **4** | **4** | **4** | **4** |

Scored zbir: **HR 8, EN 8, moderate 8, complex 8**.

---

# A. Razvojni zadaci

## 1. `q7m2-k9vx`

- **Jezik:** EN
- **Domena:** Software / technical documentation
- **Složenost:** Moderate
- **Prirodni korisnički upit:**
  “Explain how a shared HTTP cache should handle freshness, validation, and `Vary` when serving an API, and give a short implementation checklist.”
- **Zahtjevi izvedeni iz upita:**
  1. Explain freshness and expiration behavior.
  2. Explain conditional validation of stale responses.
  3. Explain how `Vary` affects cache-key selection and provide an implementation checklist.
- **Kandidatski izvori:**
  1. https://www.rfc-editor.org/rfc/rfc9110.html
  2. https://www.rfc-editor.org/rfc/rfc9111.html
  3. https://www.rfc-editor.org/rfc/rfc9112.html
  4. https://www.rfc-editor.org/rfc/rfc7234.html
  5. https://www.rfc-editor.org/rfc/rfc5861.html
  6. https://www.rfc-editor.org/rfc/rfc8246.html
  7. https://www.rfc-editor.org/rfc/rfc9211.html
  8. https://developer.mozilla.org/en-US/docs/Web/HTTP/Caching
  9. https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Vary
  10. https://developer.mozilla.org/en-US/docs/Web/HTTP/Conditional_requests

## 2. `n4cf-2wra`

- **Jezik:** HR
- **Domena:** Public policy / regulation
- **Složenost:** Complex
- **Prirodni korisnički upit:**
  “Želim ponovno koristiti skup podataka hrvatskog javnog tijela u komercijalnoj aplikaciji. Objasni kada se primjenjuju pravila o otvorenim podacima, koje naknade ili uvjeti mogu postojati, kako postupati s osobnim podacima i što provjeriti prije objave.”
- **Zahtjevi izvedeni iz upita:**
  1. Objasniti područje primjene pravila o otvorenim podacima i ponovnoj uporabi.
  2. Objasniti moguće naknade i uvjete licenciranja.
  3. Razmotriti ograničenja povezana s osobnim podacima.
  4. Razlikovati pristup informacijama od prava na ponovnu uporabu.
  5. Dati provjerljiv kontrolni popis prije komercijalne objave.
- **Kandidatski izvori:**
  1. https://eur-lex.europa.eu/eli/dir/2019/1024/oj
  2. https://eur-lex.europa.eu/legal-content/HR/TXT/?uri=CELEX:32019L1024
  3. https://data.europa.eu/en/publications/open-data-maturity
  4. https://data.europa.eu/en/using-data
  5. https://data.europa.eu/en/impact-studies/overview
  6. https://data.gov.hr/
  7. https://pristupinfo.hr/
  8. https://commission.europa.eu/law/law-topic/data-protection/data-protection-eu_en
  9. https://eur-lex.europa.eu/eli/reg/2016/679/oj
  10. https://creativecommons.org/licenses/by/4.0/

## 3. `v8hp-j3td`

- **Jezik:** EN
- **Domena:** Science / health evidence
- **Složenost:** Moderate
- **Prirodni korisnički upit:**
  “What radon level should prompt action in a home, how should I test, and what are the main proven mitigation approaches?”
- **Zahtjevi izvedeni iz upita:**
  1. Describe recognized radon reference or action levels and explain that jurisdictions may differ.
  2. Explain an appropriate home-testing process.
  3. Summarize established mitigation approaches.
- **Kandidatski izvori:**
  1. https://www.epa.gov/radon
  2. https://www.epa.gov/radon/health-risk-radon
  3. https://www.epa.gov/radon/find-radon-test-kit-or-measurement-and-mitigation-professional
  4. https://www.epa.gov/radon/epas-map-radon-zones
  5. https://www.epa.gov/radon/consumer-guide-radon-reduction
  6. https://www.epa.gov/radon/home-buyers-and-sellers-guide-radon
  7. https://www.cdc.gov/radon/about/index.html
  8. https://www.who.int/news-room/fact-sheets/detail/radon-and-health
  9. https://www.canada.ca/en/health-canada/services/health-risks-safety/radiation/radon.html
  10. https://www.gov.uk/government/collections/radon

## 4. `b2zk-6pme`

- **Jezik:** HR
- **Domena:** Consumer / product comparison
- **Složenost:** Complex
- **Prirodni korisnički upit:**
  “Usporedi kako odabrati autosjedalicu za četverogodišnje dijete između modela s pojasom u pet točaka i pomoćnog sjedala. Uključi veličinu djeteta, homologaciju, kompatibilnost s vozilom, pravilnu ugradnju i trenutak prelaska.”
- **Zahtjevi izvedeni iz upita:**
  1. Usporediti prikladnost pojasa u pet točaka i pomoćnog sjedala.
  2. Povezati izbor s visinom, masom i zrelošću djeteta.
  3. Objasniti značenje važeće homologacije.
  4. Objasniti provjeru kompatibilnosti i pravilne ugradnje u vozilu.
  5. Navesti kriterije za siguran prijelaz na sljedeću vrstu sjedala.
- **Kandidatski izvori:**
  1. https://www.nhtsa.gov/vehicle-safety/car-seats-and-booster-seats
  2. https://www.nhtsa.gov/equipment/car-seats-and-booster-seats
  3. https://www.nhtsa.gov/campaign/right-seat
  4. https://www.cdc.gov/child-passenger-safety/about/index.html
  5. https://unece.org/transport/vehicle-regulations-wp29/standards/addenda-1958-agreement-regulations-121-140
  6. https://unece.org/transport/documents/2023/03/standards/un-regulation-no-129-rev4
  7. https://road-safety.transport.ec.europa.eu/eu-road-safety-policy/priorities/safe-road-use/children_en
  8. https://www.hak.hr/hr/sigurnost-u-prometu/prometna-preventiva/
  9. https://www.faa.gov/travelers/fly_children
  10. https://www.transportation.gov/briefing-room/usdot-finalizes-new-federal-motor-vehicle-safety-standard-child-passenger-safety

---

# B. Scored zadaci

## Software / technical documentation

### 5. `r5dw-8kqa`

- **Jezik:** HR
- **Domena:** Software / technical documentation
- **Složenost:** Moderate
- **Prirodni korisnički upit:**
  “Za mobilnu aplikaciju koja prijavljuje korisnika preko vanjskog OAuth pružatelja objasni preporučeni authorization-code tijek, ulogu PKCE-a i sigurno vraćanje korisnika u aplikaciju.”
- **Zahtjevi izvedeni iz upita:**
  1. Opisati preporučeni authorization-code tijek za mobilnu odnosno native aplikaciju.
  2. Objasniti čemu služi PKCE i kako se koristi.
  3. Objasniti sigurno preusmjeravanje natrag u aplikaciju i povezane rizike.
- **Kandidatski izvori:**
  1. https://www.rfc-editor.org/rfc/rfc6749.html
  2. https://www.rfc-editor.org/rfc/rfc7636.html
  3. https://www.rfc-editor.org/rfc/rfc8252.html
  4. https://www.rfc-editor.org/rfc/rfc9207.html
  5. https://www.rfc-editor.org/rfc/rfc8414.html
  6. https://www.rfc-editor.org/rfc/rfc7591.html
  7. https://www.rfc-editor.org/rfc/rfc9126.html
  8. https://www.rfc-editor.org/rfc/rfc9700.html
  9. https://openid.net/specs/openid-connect-core-1_0.html
  10. https://datatracker.ietf.org/doc/html/draft-ietf-oauth-native-apps-2

### 6. `x1pn-4hju`

- **Jezik:** HR
- **Domena:** Software / technical documentation
- **Složenost:** Complex
- **Prirodni korisnički upit:**
  “Pregledaj plan za pristupačan web-obrazac za prijavu na događaj: opiši oznake i upute, rukovanje pogreškama, tipkovničku navigaciju, vidljivi fokus i kriterije za provjeru kontrasta te predloži testni postupak.”
- **Zahtjevi izvedeni iz upita:**
  1. Objasniti pristupačne oznake, grupiranje polja i upute.
  2. Objasniti prepoznavanje i priopćavanje pogrešaka.
  3. Pokriti potpunu uporabu tipkovnicom.
  4. Pokriti vidljivi fokus i zahtjeve kontrasta.
  5. Predložiti praktičan postupak provjere obrasca.
- **Kandidatski izvori:**
  1. https://www.w3.org/TR/WCAG22/
  2. https://www.w3.org/WAI/WCAG22/Understanding/labels-or-instructions.html
  3. https://www.w3.org/WAI/WCAG22/Understanding/error-identification.html
  4. https://www.w3.org/WAI/WCAG22/Understanding/error-suggestion.html
  5. https://www.w3.org/WAI/WCAG22/Understanding/keyboard.html
  6. https://www.w3.org/WAI/WCAG22/Understanding/focus-visible.html
  7. https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html
  8. https://www.w3.org/WAI/tutorials/forms/
  9. https://www.w3.org/WAI/test-evaluate/
  10. https://www.w3.org/WAI/ARIA/apg/patterns/

### 7. `m9gt-2cwf`

- **Jezik:** EN
- **Domena:** Software / technical documentation
- **Složenost:** Moderate
- **Prirodni korisnički upit:**
  “For a Python command-line tool, compare `venv` plus `pip` with `pipx`, and recommend which approach to use for development and which for end-user installation.”
- **Zahtjevi izvedeni iz upita:**
  1. Compare isolation and installation behavior of `venv`/`pip` and `pipx`.
  2. Recommend an approach for local development.
  3. Recommend an approach for end-user CLI installation and explain the trade-off.
- **Kandidatski izvori:**
  1. https://docs.python.org/3/library/venv.html
  2. https://docs.python.org/3/tutorial/venv.html
  3. https://docs.python.org/3/installing/index.html
  4. https://packaging.python.org/en/latest/tutorials/installing-packages/
  5. https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/
  6. https://packaging.python.org/en/latest/specifications/externally-managed-environments/
  7. https://packaging.python.org/en/latest/discussions/install-requires-vs-requirements/
  8. https://pip.pypa.io/en/stable/user_guide/
  9. https://pip.pypa.io/en/stable/topics/dependency-resolution/
  10. https://pipx.pypa.io/stable/

### 8. `c6vy-7lne`

- **Jezik:** EN
- **Domena:** Software / technical documentation
- **Složenost:** Complex
- **Prirodni korisnički upit:**
  “Create a production-readiness checklist for a Kubernetes HTTP service covering health probes, CPU and memory resources, pod security controls, disruption handling, and safe rolling updates.”
- **Zahtjevi izvedeni iz upita:**
  1. Specify appropriate startup, readiness, and liveness probe behavior.
  2. Explain CPU and memory requests and limits.
  3. Identify applicable pod-level security controls.
  4. Address voluntary disruptions and availability during maintenance.
  5. Explain configuration for safe rolling updates and rollback.
- **Kandidatski izvori:**
  1. https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/
  2. https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/
  3. https://kubernetes.io/docs/concepts/security/pod-security-standards/
  4. https://kubernetes.io/docs/concepts/security/pod-security-admission/
  5. https://kubernetes.io/docs/concepts/workloads/pods/disruptions/
  6. https://kubernetes.io/docs/tasks/run-application/configure-pdb/
  7. https://kubernetes.io/docs/concepts/workloads/controllers/deployment/
  8. https://kubernetes.io/docs/tutorials/kubernetes-basics/update/update-intro/
  9. https://kubernetes.io/docs/concepts/cluster-administration/node-shutdown/
  10. https://kubernetes.io/docs/concepts/services-networking/network-policies/

---

## Public policy / regulation

### 9. `h3qs-9btk`

- **Jezik:** HR
- **Domena:** Public policy / regulation
- **Složenost:** Moderate
- **Prirodni korisnički upit:**
  “Let mi je otkazan na putovanju iz Hrvatske u drugu državu EU-a. Objasni kada mogu birati povrat novca ili preusmjeravanje, kada može pripadati novčana naknada i koju pomoć prijevoznik mora pružiti tijekom čekanja.”
- **Zahtjevi izvedeni iz upita:**
  1. Objasniti izbor između povrata novca i preusmjeravanja.
  2. Objasniti uvjete i moguća izuzeća za novčanu naknadu.
  3. Opisati obveze skrbi i pomoći tijekom čekanja.
- **Kandidatski izvori:**
  1. https://eur-lex.europa.eu/eli/reg/2004/261/oj
  2. https://eur-lex.europa.eu/legal-content/HR/TXT/?uri=CELEX:32004R0261
  3. https://europa.eu/youreurope/citizens/travel/passenger-rights/air/index_hr.htm
  4. https://transport.ec.europa.eu/transport-themes/passenger-rights/air_en
  5. https://transport.ec.europa.eu/system/files/2022-11/2022-summary-of-the-most-relevant-cjeu-judgements.pdf
  6. https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:52016XC0615(01)
  7. https://commission.europa.eu/strategy-and-policy/policies/consumers/consumer-protection-policy/consumer-rights-travel_en
  8. https://www.ecc-croatia.hr/
  9. https://www.hakom.hr/default.aspx?id=27
  10. https://europa.eu/youreurope/citizens/travel/passenger-rights/index_hr.htm

### 10. `a8lr-5xpd`

- **Jezik:** HR
- **Domena:** Public policy / regulation
- **Složenost:** Complex
- **Prirodni korisnički upit:**
  “Mala klinika uvodi internetski portal za pacijente. Objasni kada treba provesti procjenu učinka na zaštitu podataka, koje zaštite ugraditi u sustav, kako procijeniti povredu podataka, kada obavijestiti nadzorno tijelo i kada obavijestiti pacijente.”
- **Zahtjevi izvedeni iz upita:**
  1. Objasniti kada je potrebna procjena učinka na zaštitu podataka.
  2. Opisati zaštitu podataka po dizajnu i zadanim postavkama.
  3. Objasniti procjenu rizika nastale povrede podataka.
  4. Objasniti rok i uvjete obavješćivanja nadzornog tijela.
  5. Objasniti kada je potrebno izravno obavijestiti ispitanike.
- **Kandidatski izvori:**
  1. https://eur-lex.europa.eu/eli/reg/2016/679/oj
  2. https://eur-lex.europa.eu/legal-content/HR/TXT/?uri=CELEX:32016R0679
  3. https://www.edpb.europa.eu/our-work-tools/our-documents/guidelines/guidelines-data-protection-impact-assessment-dpia-and_en
  4. https://www.edpb.europa.eu/our-work-tools/our-documents/guidelines/guidelines-42019-article-25-data-protection-design-and_en
  5. https://www.edpb.europa.eu/our-work-tools/our-documents/guidelines/guidelines-012021-examples-regarding-data-breach_en
  6. https://www.edpb.europa.eu/sme-data-protection-guide/data-breaches_en
  7. https://commission.europa.eu/law/law-topic/data-protection/rules-business-and-organisations/obligations/what-data-breach-and-what-do-we-have-do-case-data-breach_en
  8. https://commission.europa.eu/law/law-topic/data-protection/rules-business-and-organisations/obligations/when-data-protection-impact-assessment-dpia-required_en
  9. https://azop.hr/prava-ispitanika/
  10. https://azop.hr/obrazac-za-izvjescivanje-o-povredi-osobnih-podataka/

### 11. `u2fm-6jrc`

- **Jezik:** EN
- **Domena:** Public policy / regulation
- **Složenost:** Moderate
- **Prirodni korisnički upit:**
  “An EU company wants to deploy an AI system that screens job applicants. Explain how to determine whether it is high-risk, and summarize the main obligations of the provider and deployer.”
- **Zahtjevi izvedeni iz upita:**
  1. Explain how an employment-screening system is classified under the EU AI Act.
  2. Summarize obligations applicable to the system provider.
  3. Summarize obligations applicable to the organization deploying the system.
- **Kandidatski izvori:**
  1. https://eur-lex.europa.eu/eli/reg/2024/1689/oj
  2. https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689
  3. https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai
  4. https://digital-strategy.ec.europa.eu/en/faqs/navigating-ai-act
  5. https://digital-strategy.ec.europa.eu/en/policies/ai-act
  6. https://digital-strategy.ec.europa.eu/en/policies/ai-office
  7. https://digital-strategy.ec.europa.eu/en/policies/ai-pact
  8. https://commission.europa.eu/law/law-topic/data-protection/data-protection-eu_en
  9. https://www.edpb.europa.eu/our-work-tools/our-documents/opinion-board-art-64/opinion-282024-certain-data-protection-aspects_en
  10. https://eur-lex.europa.eu/eli/dir/2000/78/oj

### 12. `k7nb-1zmh`

- **Jezik:** EN
- **Domena:** Public policy / regulation
- **Složenost:** Complex
- **Prirodni korisnički upit:**
  “Prepare a compliance checklist for a US federal agency buying a public-facing web application: address Section 508 scope, the applicable technical standard, procurement language, vendor accessibility evidence, and acceptance testing.”
- **Zahtjevi izvedeni iz upita:**
  1. Explain when Section 508 applies to the acquisition.
  2. Identify the applicable web and software accessibility requirements.
  3. Describe accessibility provisions to include in procurement documents.
  4. Describe evidence that should be requested from vendors.
  5. Propose an accessibility acceptance-testing process.
- **Kandidatski izvori:**
  1. https://www.section508.gov/manage/laws-and-policies/
  2. https://www.section508.gov/manage/requirements-roadmap/
  3. https://www.section508.gov/buy/
  4. https://www.section508.gov/buy/create-solicitation/
  5. https://www.section508.gov/buy/determine-conformance/
  6. https://www.section508.gov/test/
  7. https://www.access-board.gov/ict/
  8. https://www.acquisition.gov/far/39.201
  9. https://www.acquisition.gov/far/39.203
  10. https://www.w3.org/TR/WCAG22/

---

## Science / health evidence

### 13. `p4xe-7gva`

- **Jezik:** HR
- **Domena:** Science / health evidence
- **Složenost:** Moderate
- **Prirodni korisnički upit:**
  “Kako bi grad trebao upozoriti i zaštititi stanovništvo tijekom toplinskog vala? Sažmi rizične skupine, znakove hitnih stanja i praktične mjere za kućanstva i lokalne službe.”
- **Zahtjevi izvedeni iz upita:**
  1. Identificirati skupine posebno izložene zdravstvenom riziku od vrućine.
  2. Razlikovati upozoravajuće simptome od znakova hitnog stanja.
  3. Predložiti praktične mjere za stanovništvo i lokalne službe.
- **Kandidatski izvori:**
  1. https://www.who.int/news-room/fact-sheets/detail/climate-change-heat-and-health
  2. https://www.who.int/europe/health-topics/heatwaves
  3. https://www.who.int/europe/publications/i/item/9789289071918
  4. https://climate-adapt.eea.europa.eu/en/observatory/evidence/health-effects/heat-and-health
  5. https://www.ecdc.europa.eu/en/climate-change/climate-change-europe
  6. https://www.cdc.gov/heat-health/about/index.html
  7. https://www.cdc.gov/heat-health/about/heat-and-people-with-chronic-medical-conditions.html
  8. https://www.weather.gov/safety/heat
  9. https://civilna-zastita.gov.hr/
  10. https://meteo.hr/prognoze.php?section=prognoze_specp&param=toplinski_val

### 14. `t6cj-3swy`

- **Jezik:** HR
- **Domena:** Science / health evidence
- **Složenost:** Complex
- **Prirodni korisnički upit:**
  “Odrasla osoba od 29 godina nije sigurna je li cijepljena protiv HPV-a. Objasni kome se cijepljenje preporučuje, kako se broj doza određuje prema dobi i imunološkom statusu, što se zna o sigurnosti, zašto cjepivo ne zamjenjuje probir i što treba provjeriti u hrvatskom sustavu.”
- **Zahtjevi izvedeni iz upita:**
  1. Objasniti dobne skupine za rutinsko, nadoknadno i individualno odlučivanje o cijepljenju.
  2. Objasniti kako dob pri početku i imunološki status utječu na broj doza.
  3. Sažeti poznate sigurnosne podatke i uobičajene nuspojave.
  4. Objasniti zašto cijepljenje ne zamjenjuje preporučeni probir.
  5. Navesti koje aktualne preporuke, dostupnost ili troškove treba provjeriti u Hrvatskoj.
- **Kandidatski izvori:**
  1. https://www.who.int/news-room/fact-sheets/detail/cervical-cancer
  2. https://www.who.int/teams/immunization-vaccines-and-biologicals/diseases/human-papillomavirus-vaccines-(HPV)
  3. https://www.who.int/publications/i/item/who-wer9750-645-672
  4. https://www.cdc.gov/vaccines/vpd/hpv/hcp/recommendations.html
  5. https://www.cdc.gov/hpv/about/index.html
  6. https://www.cdc.gov/vaccine-safety/vaccines/hpv.html
  7. https://www.cdc.gov/cervical-cancer/screening/index.html
  8. https://www.ecdc.europa.eu/en/publications-data/guidance-hpv-vaccination-eu-focus-boys-people-living-hiv-and-9-valent-hpv
  9. https://www.hzjz.hr/sluzba-epidemiologija-zarazne-bolesti/cijepljenje-protiv-humanog-papiloma-virusa-hpv/
  10. https://www.hzjz.hr/aktualnosti/cijepljenje-protiv-hpv-a/

### 15. `e1rd-8fqo`

- **Jezik:** EN
- **Domena:** Science / health evidence
- **Složenost:** Moderate
- **Prirodni korisnički upit:**
  “For a school trying to reduce airborne respiratory infection risk, explain how ventilation and filtration should be assessed and what practical improvements can be made without implying that they eliminate all risk.”
- **Zahtjevi izvedeni iz upita:**
  1. Explain how ventilation and filtration performance can be assessed.
  2. Recommend practical building and operational improvements.
  3. Describe limitations and place these measures within a layered-risk approach.
- **Kandidatski izvori:**
  1. https://www.cdc.gov/niosh/ventilation/about/index.html
  2. https://www.cdc.gov/niosh/ventilation/guidelines/index.html
  3. https://www.epa.gov/indoor-air-quality-iaq/ventilation-and-coronavirus-covid-19
  4. https://www.epa.gov/indoor-air-quality-iaq/air-cleaners-and-air-filters-home
  5. https://www.epa.gov/iaq-schools
  6. https://www.who.int/publications/i/item/9789240021280
  7. https://www.who.int/publications/i/item/9789240055882
  8. https://www.ashrae.org/technical-resources/filtration-disinfection
  9. https://www.ashrae.org/technical-resources/standards-and-guidelines
  10. https://www.hse.gov.uk/ventilation/index.htm

### 16. `w9ka-5nlu`

- **Jezik:** EN
- **Domena:** Science / health evidence
- **Složenost:** Complex
- **Prirodni korisnički upit:**
  “Create an evidence-based home blood-pressure monitoring plan for an adult with possible hypertension: include device selection, cuff fit, measurement technique, measurement schedule, interpretation, and urgent warning signs.”
- **Zahtjevi izvedeni iz upita:**
  1. Describe how to select a validated monitor and suitable cuff.
  2. Explain preparation, posture, and measurement technique.
  3. Propose a repeat-measurement schedule suitable for clinical review.
  4. Explain how home readings are interpreted without making an individual diagnosis.
  5. Identify readings or associated symptoms requiring urgent assessment.
- **Kandidatski izvori:**
  1. https://www.cdc.gov/high-blood-pressure/about/index.html
  2. https://www.cdc.gov/high-blood-pressure/data-research/facts-stats/index.html
  3. https://www.nhlbi.nih.gov/health/high-blood-pressure
  4. https://www.nhlbi.nih.gov/health/high-blood-pressure/diagnosis
  5. https://www.heart.org/en/health-topics/high-blood-pressure/understanding-blood-pressure-readings
  6. https://www.heart.org/en/health-topics/high-blood-pressure/monitoring-your-blood-pressure-at-home
  7. https://www.nice.org.uk/guidance/ng136
  8. https://www.uspreventiveservicestaskforce.org/uspstf/recommendation/hypertension-in-adults-screening
  9. https://www.who.int/news-room/fact-sheets/detail/hypertension
  10. https://www.validatebp.org/

---

## Consumer / product comparison

### 17. `j2hz-6mqs`

- **Jezik:** HR
- **Domena:** Consumer / product comparison
- **Složenost:** Moderate
- **Prirodni korisnički upit:**
  “Usporedi električni automobil i usporedivi benzinski automobil za 15.000 km godišnje. Objasni kako procijeniti godišnji trošak energije, emisije tijekom uporabe i praktičnost punjenja, bez pretpostavljanja jedne cijene goriva ili električne energije.”
- **Zahtjevi izvedeni iz upita:**
  1. Objasniti usporediv izračun godišnjeg troška energije uz promjenjive cijene.
  2. Usporediti emisije tijekom uporabe uz transparentne pretpostavke.
  3. Usporediti praktičnost kućnog i javnog punjenja s točenjem goriva.
- **Kandidatski izvori:**
  1. https://www.fueleconomy.gov/feg/Find.do?action=sbsSelect
  2. https://www.fueleconomy.gov/feg/evtech.shtml
  3. https://www.fueleconomy.gov/feg/label/learn-more-electric-label.shtml
  4. https://afdc.energy.gov/fuels/electricity.html
  5. https://afdc.energy.gov/calc/
  6. https://afdc.energy.gov/stations/
  7. https://www.epa.gov/greenvehicles/electric-vehicle-myths
  8. https://alternative-fuels-observatory.ec.europa.eu/
  9. https://transport.ec.europa.eu/transport-themes/clean-transport/alternative-fuels-sustainable-mobility-europe_en
  10. https://eur-lex.europa.eu/eli/reg/2023/1804/oj

### 18. `f7pu-1vbx`

- **Jezik:** HR
- **Domena:** Consumer / product comparison
- **Složenost:** Complex
- **Prirodni korisnički upit:**
  “Usporedi zračnu dizalicu topline i kondenzacijski plinski kotao za obnovu obiteljske kuće u Hrvatskoj. Uključi sezonsku učinkovitost, rad pri hladnoći, potrebnu temperaturu sustava grijanja, emisije, dimenzioniranje i informacije koje treba provjeriti na oznaci proizvoda.”
- **Zahtjevi izvedeni iz upita:**
  1. Usporediti sezonsku, a ne samo nazivnu učinkovitost.
  2. Objasniti utjecaj vanjske temperature i potrebne polazne temperature grijanja.
  3. Usporediti operativne emisije uz transparentne pretpostavke o energentima.
  4. Objasniti potrebu za proračunom toplinskog opterećenja i pravilnim dimenzioniranjem.
  5. Navesti relevantne podatke s energetske oznake i informacijskog lista proizvoda.
- **Kandidatski izvori:**
  1. https://energy-efficient-products.ec.europa.eu/product-list/space-heaters_en
  2. https://eprel.ec.europa.eu/screen/product/spaceheaters
  3. https://eur-lex.europa.eu/eli/reg_del/2013/811/oj
  4. https://eur-lex.europa.eu/eli/reg/2013/813/oj
  5. https://energy.ec.europa.eu/topics/energy-efficiency/energy-label-and-ecodesign/about_en
  6. https://www.energy.gov/energysaver/air-source-heat-pumps
  7. https://www.energy.gov/energysaver/heat-pump-systems
  8. https://www.energy.gov/energysaver/sizing-new-heating-system
  9. https://joint-research-centre.ec.europa.eu/scientific-activities-z/heat-pumps_en
  10. https://www.fzoeu.hr/hr/energetska-obnova-obiteljskih-kuca/7673

### 19. `s3gn-8ykt`

- **Jezik:** EN
- **Domena:** Consumer / product comparison
- **Složenost:** Moderate
- **Prirodni korisnički upit:**
  “Compare the security features I should look for when buying a home Wi-Fi router, focusing on update support, secure default setup, and protections for guest or untrusted devices.”
- **Zahtjevi izvedeni iz upita:**
  1. Explain how to compare update mechanisms and the expected support period.
  2. Identify secure default configuration and account-management features.
  3. Explain network separation options for guest and untrusted devices.
- **Kandidatski izvori:**
  1. https://www.cisa.gov/news-events/news/securing-wireless-networks
  2. https://www.cisa.gov/secure-our-world/secure-your-home-wifi
  3. https://www.cisa.gov/news-events/news/home-network-security
  4. https://consumer.ftc.gov/articles/how-secure-your-home-wi-fi-network
  5. https://pages.nist.gov/IoT-Device-Cybersecurity-Requirement-Catalogs/
  6. https://www.nist.gov/itl/applied-cybersecurity/nist-cybersecurity-iot-program
  7. https://www.nist.gov/publications/foundational-cybersecurity-activities-iot-device-manufacturers
  8. https://www.ncsc.gov.uk/guidance/secure-your-devices
  9. https://www.ncsc.gov.uk/collection/device-security-guidance
  10. https://www.etsi.org/technologies/consumer-iot-security

### 20. `d5mq-2rce`

- **Jezik:** EN
- **Domena:** Consumer / product comparison
- **Složenost:** Complex
- **Prirodni korisnički upit:**
  “Create a method for comparing two household washing machines sold in the EU and US using energy, water, capacity, cycle duration, and labeling information, while explaining why headline annual-cost figures may not transfer between households or countries.”
- **Zahtjevi izvedeni iz upita:**
  1. Normalize energy consumption to a comparable usage basis.
  2. Compare water consumption and rated capacity.
  3. Compare program or cycle duration.
  4. Explain the relevant EU and US label fields and test-basis differences.
  5. Explain why annual operating-cost estimates depend on usage patterns and local utility prices.
- **Kandidatski izvori:**
  1. https://energy-efficient-products.ec.europa.eu/product-list/household-washing-machines-and-washer-dryers_en
  2. https://eprel.ec.europa.eu/screen/product/washingmachines2019
  3. https://eur-lex.europa.eu/eli/reg_del/2019/2014/oj
  4. https://eur-lex.europa.eu/eli/reg/2019/2023/oj
  5. https://energy.ec.europa.eu/topics/energy-efficiency/energy-label-and-ecodesign/about_en
  6. https://www.energystar.gov/products/clothes_washers
  7. https://www.energystar.gov/products/clothes_washers/key_product_criteria
  8. https://www.energy.gov/energysaver/clothes-washers
  9. https://www.ftc.gov/business-guidance/resources/energy-labeling-rule
  10. https://www.ecfr.gov/current/title-16/chapter-I/subchapter-D/part-305

---

# Napomene o licenciranju i ponovnoj objavi

## Relativno sigurniji kandidati za arhiviranje ili reprodukciju

I dalje treba zabilježiti konkretne uvjete i datum pristupa.

- **Američke savezne agencije** (`.gov`, npr. EPA, CDC, NIST, CISA, NHTSA, DOE, FTC, USPSTF, Acquisition.gov, Access Board, eCFR): tekst koji su izradili zaposlenici savezne vlade SAD-a u pravilu je javno dobro prema 17 USC §105.
  **Oprez:** stranice mogu sadržavati fotografije, logotipe, ugrađene grafikone, standarde ili drugi materijal trećih strana.
- **Kubernetes dokumentacija:** objavljena pod **CC BY 4.0**, uz provjeru pojedinačnih ugrađenih elemenata.
- **Python dokumentacija:** PSF licenca dopušta široku reprodukciju uz zadržavanje obavijesti.
- **Python Packaging User Guide / PyPA:** uglavnom otvorena dokumentacija, ali treba potvrditi licencu konkretnog repozitorija i verzije.
- **MDN:** sadržaj je uglavnom pod **CC BY-SA 2.5 ili novijom**, a primjeri koda tipično pod CC0; atribucija i share-alike mogu biti obvezni.
- **EU pravni akti s EUR-Lexa:** pravni tekstovi i službeni materijali pokriveni su pravilima EU-a o ponovnoj uporabi; treba sačuvati izvor, datum i napomene o izmjenama te izbjegavati EU ambleme kao da predstavljaju odobrenje.
- **Europska komisija/JRC/data.europa.eu:** većina sadržaja Komisije obuhvaćena je Commission Decision 2011/833/EU i često se označava CC BY 4.0, ali status treba provjeriti na svakoj stranici.
- **W3C specifikacije i tehnike:** reprodukcija je moguća samo prema odgovarajućoj W3C Document/Software licenci i uz njezine uvjete; nije bezuvjetno javno dobro.
- **IETF/RFC Editor:** RFC-ovi su javno dostupni, ali pod pravilima **IETF Trust Legal Provisions**; distribucija cjelovitog izvornika i dopuštene izvedenice nisu isto.

## Izvori koje je vjerojatno nesigurno ponovno objaviti u cijelosti

Ove izvore koristiti kao URL + minimalni metapodatak ili pohraniti samo kada je izričita dozvola potvrđena:

1. **WHO publikacije i fact sheetovi** — WHO/IHO autorska prava; dio publikacija ima posebne licence, uključujući IGO varijante, ali uvjeti nisu jednaki za sve stavke.
2. **ECDC sadržaj** — javno dostupan, ali uvjeti reprodukcije i materijali trećih strana moraju se provjeriti po dokumentu.
3. **NICE smjernice** — Crown copyright/licencirani sadržaj, uz posebne uvjete ponovne uporabe.
4. **American Heart Association** — zaštićeni komercijalni autorskopravni sadržaj; ne republičirati cijeli tekst.
5. **ASHRAE** — standardi i stručni materijali često su strogo zaštićeni; posebno ne kopirati pune standarde.
6. **ETSI standardi i povezani dokumenti** — javno dostupni za čitanje/preuzimanje pod posebnim uvjetima, ali puna redistribucija nije automatski dopuštena.
7. **OpenID Foundation specifikacije** — primjenjuju se vlastite licence i pravila vezana uz specifikacije i implementaciju.
8. **ValidateBP.org** — program/stranica treće organizacije; nema pretpostavke javnog dobra.
9. **NCSC UK i GOV.UK** — mnogi tekstovi mogu biti pod Open Government Licence, ali logotipi, fotografije i materijali trećih strana nisu nužno obuhvaćeni.
10. **Kanadske vladine stranice** — pod Canada Open Government Licence samo gdje je tako označeno; Crown copyright i iznimke i dalje treba provjeriti.
11. **Hrvatske javne stranice** (`hzjz.hr`, `azop.hr`, `hak.hr`, `hakom.hr`, `fzoeu.hr`, `meteo.hr`, `civilna-zastita.gov.hr`, `data.gov.hr`, `pristupinfo.hr`) — javna dostupnost nije dokaz otvorene licence; tretirati kao **status neizvjestan** dok nije pronađena konkretna dozvola.
12. **Your Europe, EDPB i druge EU agencijske/board stranice** — EU reuse okvir često pomaže, ali pojedine slike, PDF-ovi, prijevodi i materijali trećih strana mogu biti izuzeti.
13. **UNECE dokumenti** — dokumenti UN-a nisu automatski javno dobro; potrebna je provjera UN-ovih pravila reprodukcije.
14. **ENERGY STAR sadržaj i oznake** — tekst američke vlade može biti javno dobro, ali znak ENERGY STAR i logotipi zaštićeni su programskim pravilima i žigovima.
15. **EPREL zapisi, slike proizvoda i proizvođački podatci** — javno su pregledljivi, ali prava nad slikama, opisima i dostavljenim dokumentima mogu pripadati dobavljačima.
16. **Proizvođačke stranice**, ako se naknadno dodaju radi konkretnih modela — gotovo sigurno su zaštićene; koristiti linkove i kratke činjenične metapodatke, ne pune preslike.

## Preporučena politika korpusa

- Za svaki URL spremiti: naslov, host, datum pristupa, promatrani datum objave/ažuriranja i URL licence/uvjeta.
- Puni tekst lokalno objaviti samo ako je utvrđen status poput public domain, CC BY, CC BY-SA, OGL ili druge kompatibilne licence.
- Kod nejasnog statusa javno objaviti samo URL, kratki činjenični metapodatak, mehanički hash i eventualno vrlo kratak dopušteni izvadak.
- Ne uključivati logotipe, fotografije, interaktivne baze, karte, standarde ili ugrađene materijale trećih strana samo zato što je okolna web-stranica otvorena.
- Prije input locka provjeriti dostupnost, preusmjeravanja, sadržajni tip i licencu svakog URL-a te zamijeniti mrtve poveznice bez mijenjanja zahtjeva zadatka.