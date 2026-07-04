# SPDX-License-Identifier: GPL-3.0-or-later
"""Normalize the Velociraptor macOS Background Task Management (BTM) artifact.

BTM (the ``backgroundtaskmanagementagent`` database, macOS 13+) records
persistence items — launch agents/daemons and login items. It shares the
``macos.persistence`` dataset, discriminated by
``raptorscope.persistence.type = btm``. Source columns confirmed against
``fixtures/velociraptor/btm_items.raw.json``.
"""
import os

from .ecs import code_signature, ecs_base


def normalize_btm(rows: list[dict], host: dict) -> list[dict]:
    docs = []
    for r in rows:
        executable = r.get("Executable") or ""

        doc = ecs_base(host, "macos.persistence")
        doc["@timestamp"] = r.get("Mtime") or ""
        if executable:
            doc["file"] = {"path": executable, "name": os.path.basename(executable)}
            process = {"executable": executable, "command_line": executable}
            sig = code_signature(r.get("CodeSignature"))
            if sig is not None:
                process["code_signature"] = sig
            doc["process"] = process
        doc["raptorscope"] = {
            "persistence": {
                "type": "btm",
                "label": r.get("Name"),
                "run_at_load": bool(r.get("Enabled")),
                "btm_type": r.get("Type"),
                "developer": r.get("Developer"),
                "uuid": r.get("UUID"),
            }
        }
        docs.append(doc)
    return docs
