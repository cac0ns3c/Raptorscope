# SPDX-License-Identifier: GPL-3.0-or-later
"""Server-side triage state — the system of record for analyst dispositions.

Keyed by ``rule_id|doc_id`` per case, each entry carries ``status`` (ack/dismissed),
``note``, and the ``actor``/``ts`` who last changed it (audit + team handoff). Held
in memory (shared across all analysts on one server) and, when ``RAPTORSCOPE_STATE_DIR``
is set, persisted to one JSON file per case so it survives restarts.
"""
import datetime
import json
import pathlib
import re


def _safe(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]", "_", name) or "_"


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class TriageStore:
    def __init__(self, dir_path: str | None = None):
        self._dir = pathlib.Path(dir_path) if dir_path else None
        if self._dir:
            self._dir.mkdir(parents=True, exist_ok=True)
        self._mem: dict[str, dict] = {}

    def _map(self, case: str) -> dict:
        if case not in self._mem:
            data: dict = {}
            if self._dir:
                f = self._dir / f"{_safe(case)}.json"
                if f.exists():
                    try:
                        data = json.loads(f.read_text())
                    except Exception:
                        data = {}
            self._mem[case] = data
        return self._mem[case]

    def _flush(self, case: str) -> None:
        if not self._dir:
            return
        try:
            (self._dir / f"{_safe(case)}.json").write_text(
                json.dumps(self._mem[case], indent=2)
            )
        except Exception:
            pass

    def get(self, case: str) -> dict:
        return {k: dict(v) for k, v in self._map(case).items()}

    def set(self, case: str, rule_id: str, doc_id: str, patch: dict, actor: str) -> dict:
        m = self._map(case)
        key = f"{rule_id}|{doc_id}"
        entry = dict(m.get(key, {}))
        for field in ("status", "note"):
            if field in patch:
                val = patch[field]
                if val:
                    entry[field] = val
                else:
                    entry.pop(field, None)
        # An entry with neither status nor note is empty — drop it.
        if not entry.get("status") and not entry.get("note"):
            m.pop(key, None)
            self._flush(case)
            return {}
        entry["actor"] = actor
        entry["ts"] = _now()
        m[key] = entry
        self._flush(case)
        return entry
