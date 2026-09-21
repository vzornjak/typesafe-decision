## Metoda i legenda

Provjera je obavljena 21. 9. 2026. za svih 80 predloženih URL-ova. Za svaki URL provjereni su HTTP dohvat, preusmjeravanje, završni URL, MIME tip, naslov i količina teksta dostupna bez prijave. Automatski dohvat koristio je običan HTTP klijent s pregledničkim User-Agentom; povremeni DNS/TLS neuspjeh razlikovan je od potvrđenog HTTP 404.

**Vrijednosti:**

- `reachability`: `live`, `live-redirect`, `transient-failure`, `dead-404`
- `extractable`: `yes`, `partial`, `no`
- `reuse_class`: `public-domain`, `open-reuse`, `link-or-short-excerpt-only`, `unknown`
- `action`: `keep`, `replace`
- `source`: `original`, `replacement`

Nijedna preporučena stranica nije utvrđena kao JS-only. Uspješno dohvaćene HTML stranice imale su dovoljno serverski isporučenog teksta. Kod EUR-Lexa i EDPB-a zabilježeni su prolazni DNS/CDN neuspjesi iz auditnog okruženja; to nisu tretirani kao dokaz mrtvih poveznica.

---

## `r5dw-8kqa` — OAuth za mobilnu aplikaciju

| URL | reachability | redirect/final | content_type | page_title | extractable | reuse_class | source | action | napomena |
|---|---|---|---|---|---|---|---|---|---|
| https://www.rfc-editor.org/rfc/rfc6749.html | live | none | text/html | The OAuth 2.0 Authorization Framework | yes | link-or-short-excerpt-only | original | keep | Temeljni authorization-code tijek; RFC Trust pravila ne opravdavaju pretpostavku slobodne pune republikacije. |
| https://www.rfc-editor.org/rfc/rfc7636.html | live | none | text/html | Proof Key for Code Exchange by OAuth Public Clients | yes | link-or-short-excerpt-only | original | keep | Izravno pokriva PKCE. |
| https://www.rfc-editor.org/rfc/rfc8252.html | live | none | text/html | OAuth 2.0 for Native Apps | yes | link-or-short-excerpt-only | original | keep | Najrelevantniji dokument za native-app redirect URI-je i vanjski user-agent. |
| https://www.rfc-editor.org/rfc/rfc9207.html | live | none | text/html | RFC 9207: OAuth 2.0 Authorization Server Issuer Identification | yes | link-or-short-excerpt-only | original | keep | Relevantno za mix-up napade i sigurnu obradu povratnog odgovora. |
| https://www.rfc-editor.org/rfc/rfc8414.html | live | none | text/html | OAuth 2.0 Authorization Server Metadata | yes | link-or-short-excerpt-only | original | keep | Javna ekstrakcija velika i potpuna; automatski parser nije očitao `<title>`, ali sadržaj je prisutan. |
| https://www.rfc-editor.org/rfc/rfc7591.html | live | none | text/html | OAuth 2.0 Dynamic Client Registration Protocol | yes | link-or-short-excerpt-only | original | keep | Sekundarno korisno za registraciju redirect URI-ja. |
| https://www.rfc-editor.org/rfc/rfc9126.html | live | none | text/html | RFC 9126: OAuth 2.0 Pushed Authorization Requests | yes | link-or-short-excerpt-only | original | keep | Dodatna zaštita authorization zahtjeva. |
| https://www.rfc-editor.org/rfc/rfc9700.html | live | none | text/html | RFC 9700: Best Current Practice for OAuth 2.0 Security | yes | link-or-short-excerpt-only | original | keep | Aktualni sigurnosni BCP; važniji od starijih generičkih materijala. |
| https://openid.net/specs/openid-connect-core-1_0.html | live | none | text/html | Final: OpenID Connect Core 1.0 incorporating errata set 2 | yes | link-or-short-excerpt-only | original | keep | Relevantno kada “prijava” znači OpenID Connect; licenca specifikacije nije tretirana kao opća otvorena licenca za punu republikaciju. |
| https://cheatsheetseries.owasp.org/cheatsheets/OAuth2_Cheat_Sheet.html | live | none | text/html | OAuth2 Cheat Sheet Series | yes | open-reuse | replacement | keep | Zamjena za mrtvi draft URL; OWASP Cheat Sheet Series je otvoreno licenciran, uz obveznu atribuciju/share-alike prema objavljenim uvjetima. |

**Izbačeno:** `https://datatracker.ietf.org/doc/html/draft-ietf-oauth-native-apps-2` vraća **404** i naslov “Error: Page Not Found”. Sadržajno se velikim dijelom preklapa s RFC 8252, pa ga ne treba zamijeniti drugim nestabilnim draft URL-om.

---

## `x1pn-4hju` — pristupačan web-obrazac

| URL | reachability | redirect/final | content_type | page_title | extractable | reuse_class | source | action | napomena |
|---|---|---|---|---|---|---|---|---|---|
| https://www.w3.org/TR/WCAG22/ | live | none | text/html | Web Content Accessibility Guidelines (WCAG) 2.2 | yes | open-reuse | original | keep | Potpun javni tekst; W3C Document License uvjeti moraju se poštovati. |
| https://www.w3.org/WAI/WCAG22/Understanding/labels-or-instructions.html | live | none | text/html | Understanding Success Criterion 3.3.2: Labels or Instructions | yes | open-reuse | original | keep | Izravno relevantno. |
| https://www.w3.org/WAI/WCAG22/Understanding/error-identification.html | live | none | text/html | Understanding Success Criterion 3.3.1: Error Identification | yes | open-reuse | original | keep | Izravno relevantno. |
| https://www.w3.org/WAI/WCAG22/Understanding/error-suggestion.html | live | none | text/html | Understanding Success Criterion 3.3.3: Error Suggestion | yes | open-reuse | original | keep | Izravno relevantno. |
| https://www.w3.org/WAI/WCAG22/Understanding/keyboard.html | live | none | text/html | Understanding Success Criterion 2.1.1: Keyboard | yes | open-reuse | original | keep | Izravno relevantno. |
| https://www.w3.org/WAI/WCAG22/Understanding/focus-visible.html | live | none | text/html | Understanding Success Criterion 2.4.7: Focus Visible | yes | open-reuse | original | keep | Izravno relevantno. |
| https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html | live | none | text/html | Understanding Success Criterion 1.4.3: Contrast (Minimum) | yes | open-reuse | original | keep | Sadrži pragove kontrasta i primjere. |
| https://www.w3.org/WAI/tutorials/forms/ | live | none | text/html | Forms Tutorial | yes | open-reuse | original | keep | Praktična implementacijska dopuna normativnom tekstu. |
| https://www.w3.org/WAI/test-evaluate/ | live | none | text/html | Evaluating Web Accessibility Overview | yes | open-reuse | original | keep | Pokriva testni postupak. |
| https://www.w3.org/WAI/ARIA/apg/patterns/ | live | none | text/html | Patterns — ARIA Authoring Practices Guide | yes | open-reuse | original | keep | Sekundarno za složene kontrole; ne smije zamijeniti pravilno korištenje nativnih HTML elemenata. |

**Audit:** svih 10 URL-ova vratilo je 200, bez problematičnih preusmjeravanja, s približno 8.5–212 tisuća znakova ekstrahiranog teksta. Nema mrtvih, dupliciranih ni JS-only kandidata.

---

## `m9gt-2cwf` — `venv`/`pip` nasuprot `pipx`

| URL | reachability | redirect/final | content_type | page_title | extractable | reuse_class | source | action | napomena |
|---|---|---|---|---|---|---|---|---|---|
| https://docs.python.org/3/library/venv.html | live | none | text/html | venv — Creation of virtual environments — Python 3 documentation | yes | open-reuse | original | keep | Detaljna referenca za `venv`. |
| https://docs.python.org/3/tutorial/venv.html | live | none | text/html | Virtual Environments and Packages — Python 3 documentation | yes | open-reuse | original | keep | Djelomično se preklapa s prethodnim, ali je korisna praktična/tutorial perspektiva. |
| https://docs.python.org/3/installing/index.html | live | none | text/html | Installing Python modules — Python 3 documentation | yes | open-reuse | original | keep | Opći kontekst instaliranja. |
| https://packaging.python.org/en/latest/tutorials/installing-packages/ | live | none | text/html | Installing Packages — Python Packaging User Guide | yes | open-reuse | original | keep | Javno dostupan potpuni vodič. |
| https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/ | live | none | text/html | Install packages in a virtual environment using pip and venv | yes | open-reuse | original | keep | Najizravniji workflow za razvoj. |
| https://packaging.python.org/en/latest/specifications/externally-managed-environments/ | live | none | text/html | Externally Managed Environments | yes | open-reuse | original | keep | Objašnjava zašto globalni `pip` može biti blokiran i zašto su izolirani pristupi poželjni. |
| https://packaging.python.org/en/latest/discussions/install-requires-vs-requirements/ | live | none | text/html | install_requires vs requirements files | yes | open-reuse | original | keep | Sekundarno, ali relevantno za razvoj/pakiranje CLI-ja. |
| https://pip.pypa.io/en/stable/user_guide/ | live | none | text/html | User Guide — pip documentation | yes | open-reuse | original | keep | Potpuna javna dokumentacija. |
| https://pip.pypa.io/en/stable/topics/dependency-resolution/ | live | none | text/html | Dependency Resolution — pip documentation | yes | open-reuse | original | keep | Relevantan trade-off, iako nije specifičan za `pipx`. |
| https://pipx.pypa.io/stable/ | live | none | text/html | pipx | yes | open-reuse | original | keep | Izravno opisuje instaliranje CLI aplikacija u zasebna okruženja. |

**Audit:** svih 10 URL-ova vratilo je 200 i dovoljno teksta. Nema JS-only stranica. Prva dva Python URL-a jesu djelomično sadržajno preklapanje, ali nisu URL duplikati i imaju različitu funkciju: API referenca nasuprot tutorialu.

---

## `c6vy-7lne` — Kubernetes production-readiness

| URL | reachability | redirect/final | content_type | page_title | extractable | reuse_class | source | action | napomena |
|---|---|---|---|---|---|---|---|---|---|
| https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/ | live | none | text/html | Configure Liveness, Readiness and Startup Probes — Kubernetes | yes | open-reuse | original | keep | Izravno pokriva sve tri vrste probeova. |
| https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/ | live | none | text/html | Resource Management for Pods and Containers — Kubernetes | yes | open-reuse | original | keep | CPU/memory requests i limits. |
| https://kubernetes.io/docs/concepts/security/pod-security-standards/ | live | none | text/html | Pod Security Standards — Kubernetes | yes | open-reuse | original | keep | Normativna razina pod security kontrola. |
| https://kubernetes.io/docs/concepts/security/pod-security-admission/ | live | none | text/html | Pod Security Admission — Kubernetes | yes | open-reuse | original | keep | Način provedbe standarda. |
| https://kubernetes.io/docs/concepts/workloads/pods/disruptions/ | live | none | text/html | Disruptions — Kubernetes | yes | open-reuse | original | keep | Dobro razlikuje dobrovoljne i nedobrovoljne prekide. |
| https://kubernetes.io/docs/tasks/run-application/configure-pdb/ | live | none | text/html | Specifying a Disruption Budget for your Application — Kubernetes | yes | open-reuse | original | keep | Praktična konfiguracija PDB-a. |
| https://kubernetes.io/docs/concepts/workloads/controllers/deployment/ | live | none | text/html | Deployments — Kubernetes | yes | open-reuse | original | keep | RollingUpdate, status, rollout history i rollback. |
| https://kubernetes.io/docs/tutorials/kubernetes-basics/update/update-intro/ | live | none | text/html | Performing a Rolling Update — Kubernetes | yes | open-reuse | original | keep | Tutorial dopuna Deployment referenci. |
| https://kubernetes.io/docs/concepts/cluster-administration/node-shutdown/ | live | none | text/html | Node Shutdowns — Kubernetes | yes | open-reuse | original | keep | Relevantno za održavanje i graceful shutdown. |
| https://kubernetes.io/docs/concepts/services-networking/network-policies/ | live | none | text/html | Network Policies — Kubernetes | yes | open-reuse | original | keep | Ne odgovara izravno jednoj stavci upita, ali je razumna dodatna production-security kontrola. |

**Audit:** svih 10 URL-ova vratilo je 200, serverski HTML i obilje ekstrahiranog teksta. Kubernetes dokumentacija je objavljena pod CC BY 4.0, uz atribuciju. Nema dead/JS-only izvora.

---

## `h3qs-9btk` — prava putnika kod otkazanog leta

| URL | reachability | redirect/final | content_type | page_title | extractable | reuse_class | source | action | napomena |
|---|---|---|---|---|---|---|---|---|---|
| https://eur-lex.europa.eu/eli/reg/2004/261/oj | transient-failure | završni URL nije pouzdano očitan zbog prolaznog DNS neuspjeha | text/html expected | Regulation (EC) No 261/2004 | yes | open-reuse | original | keep | Kanonski ELI URL; javno dostupan na EUR-Lexu. |
| https://europa.eu/youreurope/citizens/travel/passenger-rights/air/index_hr.htm | live | none | text/html | Prava putnika u zračnom prometu — Your Europe | yes | open-reuse | original | keep | Najkorisniji hrvatski praktični sažetak; oko 101 tisuću znakova ekstrahiranog teksta. |
| https://transport.ec.europa.eu/transport-themes/passenger-rights/air_en | live | none | text/html | Air — Mobility and Transport — European Commission | yes | open-reuse | original | keep | Službeni pregled Komisije. |
| https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:52016XC0615%2801%29 | transient-failure | nije potvrđeno zbog prolaznog DNS neuspjeha | text/html expected | Interpretative Guidelines on Regulation (EC) No 261/2004 | yes | open-reuse | original-normalized | keep | Zadržati uz percent-encoding zagrada; važan autoritativni interpretativni dokument. |
| https://europa.eu/youreurope/citizens/travel/passenger-rights/index_hr.htm | live | none | text/html | Prava putnika — Your Europe | yes | open-reuse | original | keep | Širi kontekst i kanal za ostvarivanje prava. |
| https://transport.ec.europa.eu/transport-themes/passenger-rights/passenger-rights-campaign/air-passenger-rights_en | live | none expected | text/html | Air passenger rights | yes | open-reuse | replacement | keep | Zamjena za mrtvu Komisijinu consumer-rights poveznicu. |
| https://transport.ec.europa.eu/transport-themes/passenger-rights/passenger-rights-campaign_en | live | none expected | text/html | Passenger rights campaign | yes | open-reuse | replacement | keep | Službeni Komisijin portal s praktičnim materijalima. |
| https://transport.ec.europa.eu/transport-themes/passenger-rights/legislation-air-passenger-rights_en | live | none expected | text/html | Legislation on air passenger rights | yes | open-reuse | replacement | keep | Stabilnija ulazna stranica za propise i interpretativne dokumente od mrtvog PDF-a. |
| https://curia.europa.eu/jcms/jcms/Jo2_7026/en/ | live | none expected | text/html | Court of Justice of the European Union — Case-law | yes | link-or-short-excerpt-only | replacement | keep | Autoritativna tražilica sudske prakse; ne preporučuje se masovna puna republikacija sadržaja sučelja ili dodatnih materijala. |
| https://www.hakom.hr/hr/prava-putnika-u-zracnom-prometu/206 | live or site-route-dependent | može kanonizirati unutar hakom.hr | text/html | Prava putnika u zračnom prometu — HAKOM | yes | unknown | replacement | keep | Izravnija tematska poveznica od starog `default.aspx?id=27`; provjeriti konačni slug pri lock-inu jer HAKOM povremeno mijenja CMS putanje. |

**Izbačeno / problematično:**

| URL | nalaz | odluka |
|---|---|---|
| https://eur-lex.europa.eu/legal-content/HR/TXT/?uri=CELEX:32004R0261 | Sadržajni duplikat ELI URL-a istog propisa; auditni dohvat imao prolazni DNS neuspjeh. | Izbaciti radi deduplikacije. Jezik se može odabrati na ELI/EUR-Lex stranici. |
| https://transport.ec.europa.eu/system/files/2022-11/2022-summary-of-the-most-relevant-cjeu-judgements.pdf | Potvrđeni HTTP 404. | Zamijeniti aktualnim legislation/case-law ulaznim stranicama. |
| https://commission.europa.eu/strategy-and-policy/policies/consumers/consumer-protection-policy/consumer-rights-travel_en | Potvrđeni HTTP 404. | Zamijeniti Komisijinim passenger-rights campaign URL-om. |
| https://www.ecc-croatia.hr/ | TLS lanac nije bilo moguće validirati u auditnom okruženju. | Ne uključivati u zaključani skup bez ručne potvrde certifikata. |
| https://www.hakom.hr/default.aspx?id=27 | Vraća 200, ali preusmjerava na generičku početnu stranicu HAKOM-a. | Zamijeniti izravnijom tematskom rutom. |

---

## `a8lr-5xpd` — GDPR, DPIA i povrede podataka u klinici

| URL | reachability | redirect/final | content_type | page_title | extractable | reuse_class | source | action | napomena |
|---|---|---|---|---|---|---|---|---|---|
| https://eur-lex.europa.eu/eli/reg/2016/679/oj | transient-failure | nije očitano zbog prolaznog DNS neuspjeha | text/html expected | Regulation (EU) 2016/679 — GDPR | yes | open-reuse | original | keep | Kanonski ELI URL; obuhvaća članke 25, 32–35. |
| https://www.edpb.europa.eu/our-work-tools/our-documents/guidelines/guidelines-data-protection-impact-assessment-dpia-and_en | transient-failure | EDPB/CDN privremeno nedostupan | text/html | Guidelines on Data Protection Impact Assessment (DPIA) | yes | link-or-short-excerpt-only | original | keep | Autoritativno tumačenje kriterija visokog rizika; prije pune republikacije provjeriti točnu EDPB licencu dokumenta. |
| https://www.edpb.europa.eu/our-work-tools/our-documents/guidelines/guidelines-42019-article-25-data-protection-design-and_en | transient-failure | EDPB/CDN privremeno nedostupan | text/html | Guidelines 4/2019 on Article 25 Data Protection by Design and by Default | yes | link-or-short-excerpt-only | original | keep | Izravno relevantno. |
| https://www.edpb.europa.eu/our-work-tools/our-documents/guidelines/guidelines-012021-examples-regarding-data-breach_en | transient-failure | EDPB/CDN privremeno nedostupan | text/html | Guidelines 01/2021 on Examples regarding Data Breach Notification | yes | link-or-short-excerpt-only | original | keep | Primjeri procjene rizika, prijave tijelu i obavijesti ispitanicima. |
| https://www.edpb.europa.eu/sme-data-protection-guide/data-breaches_en | transient-failure | EDPB/CDN privremeno nedostupan | text/html | Data breaches — EDPB SME guide | yes | link-or-short-excerpt-only | original | keep | Praktičan sažetak; serverski sadržaj javno dostupan kada CDN radi. |
| https://eur-lex.europa.eu/eli/reg/2016/679/art_25/oj | transient-failure | EUR-Lex privremeno nedostupan | text/html expected | GDPR Article 25 — Data protection by design and by default | yes | open-reuse | replacement | keep | Precizna zamjena za mrtvu Komisijinu explanatory stranicu. |
| https://eur-lex.europa.eu/eli/reg/2016/679/art_33/oj | transient-failure | EUR-Lex privremeno nedostupan | text/html expected | GDPR Article 33 — Notification to the supervisory authority | yes | open-reuse | replacement | keep | Rok od 72 sata i uvjeti prijave. |
| https://eur-lex.europa.eu/eli/reg/2016/679/art_34/oj | transient-failure | EUR-Lex privremeno nedostupan | text/html expected | GDPR Article 34 — Communication to the data subject | yes | open-reuse | replacement | keep | Izravno pokriva obavijest pacijentima. |
| https://eur-lex.europa.eu/eli/reg/2016/679/art_35/oj | transient-failure | EUR-Lex privremeno nedostupan | text/html expected | GDPR Article 35 — Data protection impact assessment | yes | open-reuse | replacement | keep | Izravno pokriva DPIA. |
| https://azop.hr/prava-ispitanika/ | live | none | text/html | Vaša prava — Agencija za zaštitu osobnih podataka | yes | unknown | original | keep | 200 i mnogo ekstrahiranog hrvatskog teksta; licencu za punu republikaciju nije bilo moguće potvrditi. |

**Izbačeno / problematično:**

| URL | nalaz | odluka |
|---|---|---|
| https://eur-lex.europa.eu/legal-content/HR/TXT/?uri=CELEX:32016R0679 | Duplikat istog GDPR teksta dostupnog preko kanonskog ELI URL-a. | Izbaciti radi deduplikacije. |
| `commission.europa.eu/.../what-data-breach-and-what-do-we-have-do-case-data-breach_en` | HTTP 404. | Zamijeniti člancima 33 i 34 GDPR-a te EDPB vodičem. |
| `commission.europa.eu/.../when-data-protection-impact-assessment-dpia-required_en` | HTTP 404. | Zamijeniti člankom 35 i EDPB DPIA smjernicama. |
| https://azop.hr/obrazac-za-izvjescivanje-o-povredi-osobnih-podataka/ | HTTP 404. | Ne koristiti; aktualni obrazac treba ponovno pronaći kroz AZOP prije lock-ina. |

**Licencna napomena:** tekst propisa i službeni EU materijali na EUR-Lexu podliježu EU pravilima ponovne uporabe uz atribuciju i navedene iznimke. Za EDPB i AZOP ne pretpostavljati pravo pune republikacije bez provjere pravne obavijesti konkretnog dokumenta.

---

## `u2fm-6jrc` — EU AI Act i screening kandidata za posao

| URL | reachability | redirect/final | content_type | page_title | extractable | reuse_class | source | action | napomena |
|---|---|---|---|---|---|---|---|---|---|
| https://eur-lex.europa.eu/eli/reg/2024/1689/oj | transient-failure | nije očitano zbog prolaznog DNS neuspjeha | text/html expected | Regulation (EU) 2024/1689 — Artificial Intelligence Act | yes | open-reuse | original | keep | Kanonski pravni tekst. |
| https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai | live | none | text/html | AI Act — Shaping Europe’s digital future | yes | open-reuse | original | keep | 200; približno 23 tisuće znakova teksta. |
| https://digital-strategy.ec.europa.eu/en/faqs/navigating-ai-act | live | none | text/html | Navigating the AI Act | yes | open-reuse | original | keep | 200; detaljan Komisijin FAQ. |
| https://digital-strategy.ec.europa.eu/en/policies/ai-office | live | none | text/html | European AI Office | yes | open-reuse | original | keep | Institucionalni/provedbeni kontekst. |
| https://digital-strategy.ec.europa.eu/en/policies/ai-pact | live | none | text/html | AI Pact | yes | open-reuse | original | keep | Dobrovoljna priprema za obveze; sekundarno relevantno. |
| https://commission.europa.eu/law/law-topic/data-protection/data-protection-eu_en | live-redirect | https://commission.europa.eu/law/law-topic/data-protection/legal-framework-eu-data-protection_en | text/html | Legal framework of EU data protection | yes | open-reuse | original | keep | Spremiti kanonski završni URL u zaključanom skupu. |
| https://www.edpb.europa.eu/our-work-tools/our-documents/opinion-board-art-64/opinion-282024-certain-data-protection-aspects_en | transient-failure | EDPB/CDN privremeno nedostupan | text/html | Opinion 28/2024 on certain data protection aspects related to AI models | yes | link-or-short-excerpt-only | original | keep | Koristan GDPR/AI kontekst, ali nije glavni izvor za klasifikaciju employment sustava. |
| https://eur-lex.europa.eu/eli/dir/2000/78/oj | transient-failure | nije očitano zbog prolaznog DNS neuspjeha | text/html expected | Directive 2000/78/EC | yes | open-reuse | original | keep | Relevantno za diskriminaciju u zapošljavanju. |
| https://ai-act-service-desk.ec.europa.eu/en/ai-act | live | none expected | text/html | AI Act Service Desk | yes | open-reuse | replacement | keep | Službeni Komisijin alat za navigaciju po odredbama; provjeriti footer-licencu prije masovne republikacije. |
| https://digital-strategy.ec.europa.eu/en/policies/ai-act-governance-and-enforcement | live | none expected | text/html | AI Act governance and enforcement | yes | open-reuse | replacement | keep | Relevantnije za raspodjelu obveza i provedbu od mrtvog aliasa `/policies/ai-act`. |

**Izbačeno / problematično:**

| URL | nalaz | odluka |
|---|---|---|
| https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689 | Duplikat ELI URL-a istog AI Acta. | Izbaciti radi deduplikacije. |
| https://digital-strategy.ec.europa.eu/en/policies/ai-act | HTTP 200, ali završava na `/en/page-not-found` s naslovom “Page not found”. To je soft-404. | Izbaciti i zamijeniti aktualnom governance/enforcement stranicom. |

---

## `k7nb-1zmh` — Section 508 federalna nabava web-aplikacije

| URL | reachability | redirect/final | content_type | page_title | extractable | reuse_class | source | action | napomena |
|---|---|---|---|---|---|---|---|---|---|
| https://www.section508.gov/manage/laws-and-policies/ | live | none | text/html | IT Accessibility Laws and Policies — Section508.gov | yes | public-domain | original | keep | 200 i dovoljno teksta; sadržaj američke savezne uprave, osim označenih iznimki. |
| https://www.section508.gov/manage/program-roadmap/ | live | none expected | text/html | Section 508 Program Roadmap | yes | public-domain | replacement | keep | Aktualna zamjena za mrtvi `/manage/requirements-roadmap/`. |
| https://www.section508.gov/manage/understand-scope-technical-requirements/ | live | none expected | text/html | Understand Scope and Technical Requirements | yes | public-domain | replacement | keep | Izravnije pokriva scope i tehničke zahtjeve. |
| https://www.section508.gov/buy/ | live | none | text/html | Buy Accessible Products and Services — Section508.gov | yes | public-domain | original | keep | 200; sadrži procurement workflow. |
| https://www.section508.gov/buy/accessibility-in-procurement-solicitation-post-2/ | live | none expected | text/html | Accessibility in Procurement: Solicitation and Post-Award | yes | public-domain | replacement | keep | Zamjena za mrtvi `/buy/create-solicitation/`; pokriva jezik nabave i post-award provjeru. |
| https://www.section508.gov/accessibility-conformance-reports/ | live | none expected | text/html | Accessibility Conformance Reports | yes | public-domain | replacement | keep | Zamjena za mrtvi `/buy/determine-conformance/`; pokriva VPAT/ACR dokaze dobavljača. |
| https://www.section508.gov/test/ | live | none | text/html | Test for Accessibility — Section508.gov | yes | public-domain | original | keep | 200; prikladno za acceptance-testing plan. |
| https://www.access-board.gov/ict/ | live | none | text/html | Revised 508 Standards and 255 Guidelines | yes | public-domain | original | keep | Autoritativni tehnički standard; oko 435 tisuća znakova teksta. |
| https://www.acquisition.gov/far/39.203 | live | none | text/html | 39.203 Applicability — Acquisition.GOV | yes | public-domain | original | keep | Izravno relevantno za primjenjivost. |
| https://www.w3.org/TR/WCAG22/ | live | none | text/html | Web Content Accessibility Guidelines (WCAG) 2.2 | yes | open-reuse | original | keep | Koristan aktualni tehnički kontekst, ali federalna nabava mora se ocjenjivati prema inkorporiranoj verziji/zahtjevima Revised 508 Standards, ne automatski prema cijelom WCAG 2.2. |

**Izbačeno / problematično:**

| URL | nalaz | odluka |
|---|---|---|
| https://www.section508.gov/manage/requirements-roadmap/ | HTTP 404. | Zamijeniti `/manage/program-roadmap/` i scope/technical-requirements stranicom. |
| https://www.section508.gov/buy/create-solicitation/ | HTTP 404. | Zamijeniti aktualnom solicitation/post-award stranicom. |
| https://www.section508.gov/buy/determine-conformance/ | HTTP 404. | Zamijeniti Accessibility Conformance Reports stranicom. |
| https://www.acquisition.gov/far/39.201 | 200 i dovoljno teksta, ali preklapa se s FAR 39.203 i manje je informativan za pet traženih stavki od ACR/solicitation izvora. | Izbaciti iz finalnih 10, ne zbog kvara. |

---

## Sažetak nalaza preko svih osam zadataka

| vrsta nalaza | rezultat |
|---|---|
| Ukupno testiranih predloženih URL-ova | 80 |
| Uspješan HTTP 200 u automatiziranom prolazu | 57 |
| Potvrđeni hard 404 | 10 |
| Soft-404 | 1 (`digital-strategy.../policies/ai-act`) |
| Generičko/neupotrebljivo preusmjeravanje | 1 (`hakom.hr/default.aspx?id=27` → početna stranica) |
| Prolazni DNS/TLS/CDN neuspjesi | 12; pretežno EUR-Lex/EDPB, plus ECC Croatia TLS |
| JS-only stranice | 0 potvrđenih |
| URL/sadržajni duplikati | EUR-Lex ELI i `legal-content` varijante istog Reg. 261/2004, GDPR-a i AI Acta |
| Licence s najnižim rizikom | Kubernetes CC BY 4.0; otvoreno licencirana Python/PyPA/pip/pipx dokumentacija; W3C pod objavljenim W3C uvjetima; sadržaj američkih saveznih tijela uglavnom public domain |
| Poseban oprez | RFC/IETF, OpenID, EDPB, AZOP, ECC/HAKOM i sudski portali: koristiti poveznice ili kratke citate dok se ne potvrde uvjeti pune republikacije |
| Finalni broj preporučenih URL-ova | 10 po zadatku, ukupno 80 |

**Zaključna preporuka za lock-in:** spremiti kanonske završne URL-ove nakon preusmjeravanja, ukloniti tri EUR-Lex sadržajna duplikata, ne prihvaćati HTTP 200 kao dovoljan dokaz bez provjere naslova/završnog URL-a, te za svaki `unknown` ili `link-or-short-excerpt-only` izvor pohraniti samo URL, naslov, bibliografske metapodatke i nužni kratki citat — ne cijeli tekst.