# SPDX-License-Identifier: GPL-3.0-or-later
"""Normalize the Velociraptor macOS Login Items artifact to ECS.

Login items are a persistence technique; they share the ``macos.persistence``
dataset and are discriminated by ``raptorscope.persistence.type = login_item``.
Source columns confirmed against ``fixtures/velociraptor/login_items.raw.json``.
"""
import os

from .ecs import code_signature, ecs_base


def normalize_login_items(rows: list[dict], host: dict) -> list[dict]:
    docs = []
    for r in rows:
        path = r.get("Path") or ""
        executable = r.get("Program") or path or None

        doc = ecs_base(host, "macos.persistence")
        doc["@timestamp"] = r.get("Mtime") or ""
        doc["file"] = {"path": path, "name": os.path.basename(path)}
        if r.get("User"):
            doc["user"] = {"name": r.get("User")}
        if executable:
            process = {"executable": executable, "command_line": executable}
            sig = code_signature(r.get("CodeSignature"))
            if sig is not None:
                process["code_signature"] = sig
            doc["process"] = process
        doc["raptorscope"] = {
            "persistence": {
                "type": "login_item",
                "label": r.get("Name"),
                "run_at_load": True,
                "hidden": bool(r.get("Hidden")),
            }
        }
        docs.append(doc)
    return docs
