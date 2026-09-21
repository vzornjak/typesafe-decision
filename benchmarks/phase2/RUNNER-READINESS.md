# Scored runner readiness audit — 2026-09-21

Status: **NO-GO for scored API calls**.

The read-only audit found five P0 blockers and five P1 comparability risks. The following are addressed offline on the Phase 2 branch: randomized arm-specific candidate order, strict candidate ID/mode checks, prompt ceiling, portable 160-artifact rehearsal, actual MAIN CLI response fixture and strict parser, full code/policy supplementary manifest coverage, and a separate output-seal wrapper that rejects incomplete or failed answers. Original input lock is not rewritten.

**Still blocking live scored execution:**

1. Failure artifacts now use `null` for unknown billed usage and preserve known Jev `total_usage` and MAIN provider-reported tokens when available. However a Jev transport exception before `rank()` returns or a MAIN CLI failure without a parseable response can still leave actual billed usage unknown. Actual total-cost break-even cannot pass if that occurs.
2. D-001 requires an OS-enforced gold-inaccessible runner. Local iSH probes failed: shared-mount permissions were ineffective; mount namespaces are unavailable; chroot escapes through `..`. See `ISOLATION-FEASIBILITY.md`. **No scored calls on this device.**
3. An independent final GO audit on the exact executable commit is still required. The latest read-only audit remained NO-GO.
4. The supplementary runner lock must be regenerated for the final reviewed commit in the isolated runner. Any previous local runner lock is stale after code changes.
5. Positive 160-completion and negative failure/missing/unknown-usage output tests now pass. Prompt-hash reconstruction, accounting under all failure shapes, and mandatory enforcement of the supplementary seal against direct use of the historical lock command remain unresolved.
6. `PREREGISTRATION.md` and `config/design.json` were frozen as draft labels in the original immutable input lock. This inconsistency must be documented as provenance, not silently rewritten.

No scored Jev or MAIN call is permitted while this file says NO-GO. Development Jev calls and a single non-scored MAIN CLI shape smoke are not Phase 2 scored evidence. Do not merge this branch as a claim of Phase 2 completion.
