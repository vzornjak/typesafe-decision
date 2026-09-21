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

Fetched text remains under gitignored `source-cache/`, while the audited local materialization and runner bundle remain under gitignored `materialized-scored/` and `runner-inputs/`. Git stores only content-free hash commitments and provenance. Runner-visible scored placeholder files in the public tree are not used by the lock tool when the local runner bundle exists.

Materialization completed after browser fallback and three documented no-gold source-plan amendments:

- technical availability: `160/160`;
- local materialized corpus audit: `160/160`, zero errors;
- materialized aggregate SHA-256: `1f2bfc8f13ea4860c6f9803dd94489baa80fdb3a48c1c42aee6a1bea7c2baa1b`;
- local runner bundle: 16 scored tasks / 160 candidates;
- runner aggregate SHA-256: `bab794731534bea13d483adbafe09dade6a1b46edf935f845bb04da658c38ad8`;
- maximum no-rank candidate content: 105,633 characters under the frozen 120,000-character ceiling.

No third-party source text is published in git. Every local row records attribution, transport, final URL, reuse class, byte/content hash and excerpt limit. `unknown` and `link-or-short-excerpt-only` rows are capped at 1,200 characters; reviewed `public-domain` and `open-reuse` rows are capped at 12,000.

This checkpoint is not benchmark evidence, does not expose gold and does not itself permit scored model execution. Input lock, sealed-gold validation and pre-unblind barriers remain mandatory.
