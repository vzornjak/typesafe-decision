#!/usr/bin/env python3
"""Record the actual routing choice and outcome for a logged decision.

Privacy policy (phase 1): the audit log stays content-free. `--note` is NOT
written to the log; only its length and a fingerprint are recorded, and the
note itself is echoed back on stdout for the caller to keep wherever it
manages sensitive text. Use `--allow-note-in-log` to opt in explicitly when
the deployment has accepted that the log then holds free text.
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ts_common as tsc  # noqa: E402

VALID = {"main", "sub", "general", "max"}
NOTE_MAX = 300


def build(argv=None):
    p = tsc.JSONArgumentParser(description="Record actual routing choice and outcome")
    p.add_argument("--decision-id", required=True)
    p.add_argument("--actual", required=True, choices=sorted(VALID))
    p.add_argument("--success", choices=["yes", "no", "unknown"], default="unknown")
    p.add_argument("--escalated", action="store_true")
    p.add_argument("--note", default="")
    p.add_argument("--allow-note-in-log", action="store_true",
                   help="explicitly accept free text in the audit log (off by default)")
    p.add_argument("--log-path", default=None)
    return p.parse_args(argv)


def run(a):
    tsc.load_config()
    log = tsc.log_path(a.log_path)
    if not log.exists():
        return {"recorded": False, "error": "no_decision_log", "log_path": str(log)}, None
    rows = []
    for line in log.read_text(encoding="utf-8").splitlines():
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    known = any(isinstance(r, dict) and r.get("event", "decision") == "decision"
                and r.get("decision_id") == a.decision_id for r in rows)
    if not known:
        return {"recorded": False, "error": "unknown_decision_id",
                "decision_id": a.decision_id}, None
    row = {"event": "outcome", "schema_version": tsc.SCHEMA_VERSION, "decision_id": a.decision_id,
           "ts": int(time.time()), "actual_executor": a.actual, "success": a.success,
           "escalated": bool(a.escalated)}
    note = str(a.note or "")
    if note:
        # Content-free by default: length plus an opaque fingerprint only.
        row["note_len"] = min(len(note), NOTE_MAX)
        row["note_ref"] = tsc.opaque_id(note[:NOTE_MAX])
        if a.allow_note_in_log:
            row["note"] = note[:NOTE_MAX]
            row["note_policy"] = "explicitly_allowed_free_text"
        else:
            row["note_policy"] = "omitted_from_log"
    _, log_error = tsc.write_log(row, a.log_path)
    out = {"recorded": log_error is None, **row}
    if note and not a.allow_note_in_log:
        out["note_echo"] = note[:NOTE_MAX]
        out["warnings"] = ["note_omitted_from_log"]
    if log_error:
        out["log_error"] = log_error
    return out, None


def main(argv=None):
    exc = None
    try:
        a = build(argv)
        out, _ = run(a)
    except SystemExit as e:
        return tsc.EXIT_USAGE if e.code else tsc.EXIT_OK
    except Exception as e:  # noqa: BLE001 - boundary must always emit valid JSON
        exc = e
        out = {"recorded": False, "error_type": type(e).__name__, "error": str(e)[:240],
               "warnings": ["failed_closed"]}
        if isinstance(e, tsc.ConfigError):
            out["config_errors"] = tsc.config_errors()
    return tsc.emit(out, exc)


if __name__ == "__main__":
    sys.exit(main())
