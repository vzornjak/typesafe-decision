# Scored runner readiness audit — 2026-09-21

Status: **NO-GO for scored API calls**.

The read-only audit found five P0 blockers and five P1 comparability risks. The following are addressed offline on the Phase 2 branch: randomized arm-specific candidate order, strict candidate ID/mode checks, prompt ceiling, portable 160-artifact rehearsal, actual MAIN CLI response fixture and strict parser, full code/policy supplementary manifest coverage, and a separate output-seal wrapper that rejects incomplete or failed answers. Original input lock is not rewritten.

**Still blocking live scored execution:**

1. The runner's exception path records known/unknown billed Jev/MAIN usage as zeros. That invalidates actual-cost accounting. Partial Jev `total_usage` and `unaccepted_usage`, MAIN post-billing failures, and attempt/response metadata require explicit preservation; unknown is not zero.
2. The full scored runner must be executed in an isolated gold-inaccessible filesystem/process per D-001, not just with environment-name filtering. That custody evidence is not yet established.
3. The new runner code has not yet obtained a terminal independent GO review after all P0 fixes. A green CI is necessary but not sufficient.
4. The supplementary runner lock must be generated only after final reviewed code is committed and CI passes. There must be a byte-identical dry-run in the isolated execution environment.
5. The output seal needs positive and negative offline contract tests covering 160 completed rows, one failed row, missing rows, wrong model/usage and wrong prompt hash before it can authorize the historical output-lock command.

No scored Jev or MAIN call is permitted while this file says NO-GO. Development Jev calls and a single non-scored MAIN CLI shape smoke are not Phase 2 scored evidence. Do not merge this branch as a claim of Phase 2 completion.
