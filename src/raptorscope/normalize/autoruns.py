# SPDX-License-Identifier: GPL-3.0-or-later
"""Normalize the real Velociraptor ``MacOS.Detection.Autoruns`` artifact to ECS.

Unlike the synthetic per-type fixtures (launch_items / login_items / cron_items),
the genuine Velociraptor collection emits **one** ``MacOS.Detection.Autoruns``
artifact whose rows are discriminated by a ``Source`` and carry per-source columns
plus a nested config blob (``LaunchdConfig`` / ``LoginItemConfig``) and a file
``Hash`` (there is no flat ``CodeSignature`` here). Every row maps to a
``macos.persistence`` doc, matching the shape the rest of the pipeline (and the
paired detections) already consume.

See docs/spikes/2026-07-04-real-velociraptor-validation.md for the schema deltas.
"""
import os

from .ecs import code_signature, ecs_base

# Autoruns `Source` (lowercased) -> our persistence type.
_SOURCE_TYPE = {
    "launchagents": "launch_agent",
    "launch agents": "launch_agent",
    "launchdaemons": "launch_daemon",
    "launch daemons": "launch_daemon",
    "loginitems": "login_item",
    "login items": "login_item",
    "sandboxed loginitems": "login_item",
    "startupitems": "startup_item",
    "startup items": "startup_item",
    "cron": "cron",
    "crontab": "cron",
    "crontabs": "cron",
    "btm": "btm",
    "backgroundtaskmanagement": "btm",
}

_CRON_FIELDS = ("Minute", "Hour", "DayOfMonth", "Month", "DayOfWeek")


def _persistence_type(source: str, path: str) -> str:
    key = (source or "").strip().lower()
    if key in _SOURCE_TYPE:
        return _SOURCE_TYPE[key]
    # Fall back to a path heuristic when Source is absent/unknown.
    p = path or ""
    if "LaunchAgents" in p:
        return "launch_agent"
    if "LaunchDaemons" in p:
        return "launch_daemon"
    if "cron" in p:
        return "cron"
    return "launch_agent"


def _hash_value(raw) -> str | None:
    """Autoruns ``Hash`` may be a bare string or a ``{SHA256: ...}`` object."""
    if isinstance(raw, dict):
        for k in ("SHA256", "Sha256", "sha256", "MD5", "SHA1"):
            if raw.get(k):
                return str(raw[k])
        return None
    return str(raw) if raw else None


def _cron_schedule(row: dict) -> str | None:
    parts = [str(row[f]) for f in _CRON_FIELDS if row.get(f) not in (None, "")]
    return " ".join(parts) if parts else row.get("Schedule")


def normalize_autoruns(rows: list[dict], host: dict) -> list[dict]:
    """Map ``MacOS.Detection.Autoruns`` rows to one ``macos.persistence`` doc each."""
    docs = []
    for r in rows:
        source = r.get("Source") or r.get("Type") or ""
        path = r.get("OSPath") or r.get("File") or r.get("Path") or ""
        ptype = _persistence_type(source, path)

        # Nested launchd/login-item config carries the real program + label.
        config = r.get("LaunchdConfig") or r.get("LoginItemConfig") or {}
        if not isinstance(config, dict):
            config = {}

        args = (
            config.get("ProgramArguments")
            or r.get("ProgramArguments")
            or r.get("Args")
            or []
        )
        if isinstance(args, str):
            args = [args]
        program = (
            r.get("Program")
            or config.get("Program")
            or (args[0] if args else None)
        )
        command = r.get("Command")  # cron source

        doc = ecs_base(host, "macos.persistence")
        doc["@timestamp"] = r.get("Mtime") or ""
        doc["file"] = {"path": path, "name": os.path.basename(path)}
        if r.get("User"):
            doc["user"] = {"name": r.get("User")}

        if ptype == "cron" and command:
            executable = command.split()[0] if command.split() else command
            doc["process"] = {"executable": executable, "command_line": command}
        elif program:
            cmdline = " ".join([program, *args[1:]]) if args else program
            doc["process"] = {"executable": program, "command_line": cmdline}

        # Signature enrichment: MacOS.Raptorscope.SignedAutoruns adds a
        # CodeSignature object (stock Autoruns emits only a Hash). Attach it even
        # for items with no explicit program (e.g. login items = an .app bundle).
        sig = code_signature(r.get("CodeSignature"))
        if sig is not None:
            doc.setdefault("process", {})["code_signature"] = sig

        persistence: dict = {
            "type": ptype,
            "label": config.get("Label") or r.get("Label") or r.get("Name"),
            "run_at_load": bool(config.get("RunAtLoad") or r.get("RunAtLoad")),
        }
        h = _hash_value(r.get("Hash"))
        if h:
            persistence["hash"] = h
        if r.get("Disabled") is not None:
            persistence["disabled"] = bool(r.get("Disabled"))
        if ptype == "cron":
            persistence["schedule"] = _cron_schedule(r)
        if r.get("Hidden") is not None:
            persistence["hidden"] = bool(r.get("Hidden"))
        doc["raptorscope"] = {"persistence": persistence}
        # Autoruns times are file Mtime, not a true event time — mark provenance.
        doc["raptorscope"]["time"] = {"source": "mtime"}
        docs.append(doc)
    return docs
