# SPDX-License-Identifier: GPL-3.0-or-later
"""Normalize macOS Unified Log (tracev3 / .logarchive) entries to ECS.

Phase 1 of raw-evidence ingestion (no Velociraptor). The ``macos-UnifiedLogs``
parser emits one JSONL row per log entry (``subsystem``, ``category``,
``process``, ``pid``, ``message``, ``timestamp``). Unlike EVTX's discrete events,
Unified Logs are semi-structured message lines — a single logical event is
reconstructed by *correlating* related lines and *extracting* fields from the
free-text message.

Phase-0 predicate: **TCC access requests** (``subsystem = com.apple.TCC``). A
request is a multi-line sequence keyed by ``msgID`` (validated against real output
2026-07-07):

    AUTHREQ_CTX:     msgID=X, ... service=kTCCServiceScreenCapture, preflight=yes
    AUTHREQ_SUBJECT: msgID=X, subject=com.apple.Terminal
    AUTHREQ_RESULT:  msgID=X, authValue=1, ...

We emit one ``macos.unifiedlog`` doc per completed request — reusing the
``raptorscope.tcc.*`` fields (same shape as the TCC.db-sourced ``macos.tcc``
dataset) so the signal is familiar, plus ``raptorscope.unifiedlog.*`` provenance.
``authValue``: 2 = allowed (matching TCC.db semantics); lower values are a query /
denial.
"""
import re

from .ecs import ecs_base

_MSGID = re.compile(r"msgID=([0-9.]+)")
_SERVICE = re.compile(r"service=(kTCCService\w+)")
_SUBJECT = re.compile(r"subject=([^,\n]+)")
_AUTHVAL = re.compile(r"authValue=(\d+)")

# authd (com.apple.Authorization): a right grant is correlated to its requesting
# process by the ``engine N`` id shared between the "evaluates" and "granting" lines.
_ENGINE = re.compile(r"engine (\d+)")
_EVAL = re.compile(r"Process (\S+) \(PID (\d+)\) evaluates")
_GRANT = re.compile(r"granting right ([\w.]+)")


def normalize_unifiedlog(rows: list[dict], host: dict) -> list[dict]:
    """Dispatch each supported Unified Log subsystem to its own extractor."""
    return _normalize_tcc(rows, host) + _normalize_authd(rows, host)


def _normalize_tcc(rows: list[dict], host: dict) -> list[dict]:
    # Correlate the AUTHREQ_* lines of each request by msgID.
    reqs: dict[str, dict] = {}
    for r in rows:
        if r.get("subsystem") != "com.apple.TCC":
            continue
        msg = r.get("message") or ""
        mid = _MSGID.search(msg)
        if not mid:
            continue
        d = reqs.setdefault(mid.group(1), {})
        # RESULT is emitted last, so keep advancing the timestamp to the newest line.
        d["ts"] = r.get("timestamp") or d.get("ts")
        d.setdefault("process", r.get("process"))
        d.setdefault("pid", r.get("pid"))
        if msg.startswith("AUTHREQ_CTX"):
            m = _SERVICE.search(msg)
            if m:
                d["service"] = m.group(1)
        elif msg.startswith("AUTHREQ_SUBJECT"):
            m = _SUBJECT.search(msg)
            if m:
                d["subject"] = m.group(1).strip().rstrip(",").strip()
        elif msg.startswith("AUTHREQ_RESULT"):
            m = _AUTHVAL.search(msg)
            if m:
                d["auth_value"] = int(m.group(1))

    docs = []
    for mid, d in reqs.items():
        # Only a request that resolved to a concrete service is detection-worthy.
        if "service" not in d:
            continue
        subject = d.get("subject")
        is_path = bool(subject) and subject.startswith("/")
        doc = ecs_base(host, "macos.unifiedlog")
        doc["@timestamp"] = d.get("ts") or ""
        doc["event"]["action"] = "tcc_access_request"
        if is_path:
            doc["process"] = {"executable": subject}
        doc["raptorscope"] = {
            "tcc": {
                "service": d.get("service"),
                "client": subject,
                "client_type": "path" if is_path else "bundle_id",
                "allowed": d.get("auth_value", 0) >= 2,
            },
            "unifiedlog": {
                "subsystem": "com.apple.TCC",
                "category": "access",
                "process": d.get("process"),
                "pid": d.get("pid"),
                "msg_id": mid,
            },
        }
        docs.append(doc)
    return docs


def _normalize_authd(rows: list[dict], host: dict) -> list[dict]:
    """Authorization right grants: correlate requesting process ↔ granted right
    by the shared ``engine`` id (validated against real output 2026-07-07)."""
    procs: dict[str, tuple] = {}   # engine -> (executable, pid, ts)
    grants: list[tuple] = []       # (engine, right, ts)
    for r in rows:
        if r.get("subsystem") != "com.apple.Authorization":
            continue
        msg = r.get("message") or ""
        eng = _ENGINE.search(msg)
        if not eng:
            continue
        e = eng.group(1)
        ev = _EVAL.search(msg)
        if ev:
            procs[e] = (ev.group(1), ev.group(2), r.get("timestamp"))
        g = _GRANT.search(msg)
        if g:
            grants.append((e, g.group(1), r.get("timestamp")))

    docs = []
    for e, right, ts in grants:
        proc, pid, pts = procs.get(e, (None, None, None))
        doc = ecs_base(host, "macos.unifiedlog")
        doc["@timestamp"] = ts or pts or ""
        doc["event"]["action"] = "authorization_right"
        if proc:
            doc["process"] = {"executable": proc, "pid": int(pid) if pid else None}
        doc["raptorscope"] = {
            "unifiedlog": {
                "subsystem": "com.apple.Authorization",
                "category": "authorization",
                "process": proc,
                "pid": int(pid) if pid else None,
                "right": right,
                "granted": True,
            },
        }
        docs.append(doc)
    return docs
