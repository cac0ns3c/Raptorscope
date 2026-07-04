# SPDX-License-Identifier: GPL-3.0-or-later
"""Normalize the Velociraptor macOS launch-item persistence artifact to ECS.

Source column names are confirmed against
``fixtures/velociraptor/launch_items.raw.json`` (see the Task 2 spike note).
"""
import os

from .ecs import code_signature, ecs_base


def _persistence_type(path: str) -> str:
    return "launch_agent" if "LaunchAgents" in (path or "") else "launch_daemon"


def normalize_launch_items(rows: list[dict], host: dict) -> list[dict]:
    """Map captured launch-item rows to one ECS doc each."""
    docs = []
    for r in rows:
        path = r.get("Path") or r.get("OSPath") or ""
        program = r.get("Program")
        args = r.get("ProgramArguments") or []
        if isinstance(args, str):
            args = [args]
        executable = program or (args[0] if args else None)
        cmdline = " ".join([program, *args]) if program else " ".join(args)

        doc = ecs_base(host, "macos.persistence")
        doc["@timestamp"] = r.get("Mtime") or r.get("_ts") or ""
        doc["file"] = {"path": path, "name": os.path.basename(path)}

        if executable:
            process: dict = {
                "executable": executable,
                "command_line": cmdline or executable,
            }
            sig = code_signature(r.get("CodeSignature"))
            if sig is not None:
                process["code_signature"] = sig
            doc["process"] = process

        doc["raptorscope"] = {
            "persistence": {
                "type": _persistence_type(path),
                "label": r.get("Label"),
                "run_at_load": bool(r.get("RunAtLoad")),
            },
            "time": {"source": "mtime"},  # plist file-modified time, not event time
        }
        docs.append(doc)
    return docs
