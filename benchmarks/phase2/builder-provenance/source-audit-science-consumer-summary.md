# Scored source-audit summary — science, health and consumer tasks

Audit date: 2026-09-21
Auditor role: isolated read-only source auditor
Gold labels visible: no

The full terminal callback was reviewed before source extraction. This summary preserves the actionable findings without claiming that a URL is evidence or gold.

## Cross-task findings

- No literal URL duplicates across the eight tasks.
- CDC pages tested for tasks 13–16 returned automated-client `403 Access Denied`; they are public-domain candidates but unreliable for reproducible fetching.
- EUR-Lex ELI URLs in tasks 17, 18 and 20 had transient network failures, not confirmed 404s.
- EPREL pages in tasks 18 and 20 were thin/JavaScript-only and cannot be the sole text source.
- AHA, ASHRAE, ETSI, ValidateBP/STRIDE BP and IEA content is link-or-short-excerpt-only unless separate reuse permission is established.
- WHO, UK OGL, EU reuse-policy and US federal public-domain sources still require per-item attribution and third-party-material checks.
- Tasks 18 and 20 need the most source replacement work.

## Task findings

- `p4xe-7gva` heat: replace generic ECDC and Civil Protection landing pages; prefer WHO heat guidance, weather.gov/ready.gov and a specific warning page.
- `t6cj-3swy` HPV: replace dead ECDC and automation-blocked CDC pages with WHO, HZJZ, NHS, NCI and EMA sources.
- `e1rd-8fqo` ventilation: replace a dead WHO permalink and generic ASHRAE catalog; prefer EPA schools/ventilation, WHO roadmap, HSE and one ASHRAE topical page.
- `w9ka-5nlu` blood pressure: replace or supplement blocked CDC/AHA sources with NHLBI, USPSTF, WHO, NICE/NHS and a validated-device registry linked only as allowed.
- `j2hz-6mqs` EV: original set is mostly usable; interactive calculators/station maps are dynamic and cannot be the sole textual evidence.
- `f7pu-1vbx` heat pumps: six proposed URLs were confirmed 404, two EUR-Lex URLs were transiently unavailable, and EPREL was JS-only; reconstruct the set before lock.
- `s3gn-8ykt` router security: replace dead CISA/NCSC links and the generic ETSI redirect; prefer CISA, FTC, NIST, current NCSC/GOV.UK guidance.
- `d5mq-2rce` washing machines: replace old EC/DOE/FTC URLs; EPREL is JS-only and eCFR was anti-bot redirected; prefer current EC product page, EUR-Lex regulations, ENERGY STAR and stable US regulatory documents.

## Lock rule

Every final candidate must be re-fetched by the production source extractor. The locked provenance row must record requested URL, canonical final URL, HTTP status, MIME type, page title, observed date, reuse class, extraction method, excerpt/full-text policy, content SHA-256 and character count. A failed, blocked, soft-404, generic redirect or unresolved license cannot silently enter the input bundle.
