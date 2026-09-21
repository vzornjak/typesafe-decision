# D-001 OS isolation feasibility — local iSH/Alpine

Date: 2026-09-21
Status: **LOCAL OS ISOLATION FAILED — SCORED RUN NO-GO**

Requirement: the scored runner must not be able to read sealed scored gold or gold-derived callback details. This is a custody gate, not a model prompt preference.

Read-only feasibility probes (no gold file contents opened, no model calls):

- Running the process as Unix user `nobody` does not deny reading the sealed-gold path; shared mount reports permissive effective permissions.
- `chmod 700` on the shared directory did not persist: `stat` still reported `755`; it cannot serve as a separation boundary here.
- `unshare -m` reports `Function not implemented`.
- A temporary `chroot` with BusyBox and musl loader starts, but `/../../var/minis/workspace/...` inside it resolves to the host workspace and can enumerate the sealed-gold directory's metadata. The chroot therefore does not confine paths on this iSH system.

**Conclusion:** the local iSH shell does not provide a tested OS mechanism that can make the scored runner gold-inaccessible. No scored Jev/MAIN calls may run in this environment under D-001.

## Acceptable next environment

Use a separate trusted host with a genuine container/mount namespace or equivalent independently verified OS boundary. The sealed gold must remain on the coordinator side and **never** be copied/mounted into the runner environment. Transfer only the locked runner inputs, code, required credentials, and a designated output destination. Before paid calls, prove from inside the exact runner context that a probe for the gold path is denied/nonexistent, the expected input lock and runner lock verify, and the environment contains no gold-derived data. Capture that proof and an immutable image/worktree digest. After completion, transfer sealed outputs back, validate all 160 records, lock them, then unblind gold on the evaluator side only.

Do not treat app-level subagent session separation or an instruction to “ignore gold” as an OS boundary.
