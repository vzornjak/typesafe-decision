# Minis OAuth relay feasibility — Phase 2

Date: 2026-09-21
Status: **NON-SCORED TRANSPORT SMOKE PASS; SCORED RUN STILL NO-GO**

## Architecture

The gold-free Docker runner sends a signed, hash-checked MAIN request through an SSH reverse tunnel to a loopback-only relay in Minis. The relay calls `minis-model-use` under the existing Minis Anthropic OAuth login and returns the served model, stop reason, answer and provider-reported usage. OAuth credentials are never transmitted to macserver or Docker.

- Server: `relay_minis.py`, binds `127.0.0.1:18766`; HMAC-authenticated JSON, 32-character unique nonce, fixed model (`claude-opus-5`), fixed system prompt SHA-256, max output tokens and temperature.
- Client: `main_relay.py`, validates echoed user/system hashes, model, stop reason and usage.
- SSH: reverse `127.0.0.1:18767` on macserver to `127.0.0.1:18766` in Minis; not a public/Tailscale-facing service.
- Docker: `--network host` was needed for loopback-only reverse tunnel. The container must still have an allowlisted read-only filesystem; host-network egress is a separate risk to assess and constrain before scored execution.

## Evidence

- Offline relay tests: four checks passed (unsigned request rejected; exact user prompt; served model/usage round trip; nonce used once).
- GitHub CI on relay commit `c8ba3ba381db4a9897f39d544ad8a4025fa321a4`: success.
- One non-scored Mac-host smoke: served `claude-opus-5`, reported 255 input/4 output tokens.
- One non-scored Docker smoke: served `claude-opus-5`, reported 253 input/245 output tokens. The wording produced a longer response; no result quality was assessed.
- No scored input, gold, or corpus source was sent to the relay during these probes.
- Trial relay process and temporary HMAC secret were removed after testing. The SSH reverse forward may remain listening but cannot authenticate without the deleted secret.

## Remaining NO-GO items

1. Relay currently trusts requests from the caller if it holds the HMAC key; the relay lives in the same Minis filesystem as sealed gold. Prove the server process does not inspect gold or gold-derived context, and ensure the exact locked relay bytes are attested. The host cannot enforce this against a malicious relay process; this is a trusted transport boundary requiring independent custody audit.
2. The runner itself still cannot pass preflight from the curated 47-file Docker allowlist, because the historical input lock covers 91 files including an excluded gold-derived deviation note. A scoped attestation is required; do not mount the excluded files merely to satisfy the verifier.
3. Actual total-cost accounting, output-seal bypass, prompt reconstruction and terminal independent GO remain outstanding in `RUNNER-READINESS.md`.
4. Test that the user's OAuth plan permits the full workload. Do not use this relay to bypass provider terms, throttling or billing restrictions.

This file records transport feasibility only. It does not authorize scored calls or close P0-6.
