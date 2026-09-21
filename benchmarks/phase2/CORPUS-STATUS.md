# Scored corpus materialization status

Status: **IN PROGRESS — INPUT LOCK FORBIDDEN**

Date: 2026-09-21

## Final source plan

Two independent read-only audits reviewed all 160 proposed URLs without gold access. The plan was revised to remove confirmed 404s, soft-404s, generic redirects and duplicate legal texts while preserving a mixture of relevant, partially relevant and distractor candidates.

The repository contains content-free source-plan rows with URL and conservative reuse class. It does not yet publish fetched third-party text.

## First production-fetch checkpoint

- candidates attempted: 160
- accepted by transport/content checks: 118
- rejected: 42

Rejections include shell-only DNS/TLS failures, confirmed 404/403 responses, anti-bot pages, JavaScript-only shells and extracts below the initial 500-character threshold. Browser transport independently confirmed that representative EUR-Lex, EDPB and NICE sources are live, so a shell DNS failure is not treated as proof that a source is dead.

The minimum extract threshold was subsequently calibrated to 150 characters for legitimate short regulatory or interactive candidates. Empty shells, soft-error pages and anti-bot responses remain forbidden.

## Publication boundary

Fetched text remains under gitignored `source-cache/`. Runner-visible scored task files remain placeholders. No third-party excerpt enters git until:

1. requested and final URL are stable;
2. status, MIME type, title, date and raw hash are recorded;
3. excerpt is long enough and not an error/anti-bot/JS shell;
4. reuse class and attribution are reviewed per source;
5. sources limited to linking/short quotation use remain within a documented excerpt limit;
6. a fresh scan confirms no accidental private or gold data.

This checkpoint is not benchmark evidence, does not expose gold and does not permit scored model execution.
