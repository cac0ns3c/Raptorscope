# SPDX-License-Identifier: GPL-3.0-or-later
"""Normalize the Velociraptor macOS Background Task Management (BTM) artifact.

BTM (the ``backgroundtaskmanagementagent`` database, macOS 13+) records
persistence items — launch agents/daemons and login items. It shares the
``macos.persistence`` dataset, discriminated by
``raptorscope.persistence.type = btm``. Source columns confirmed against
``fixtures/velociraptor/btm_items.raw.json`` and, on real data (2026-07-05), the
``sfltool dumpbtm`` output the custom artifact parses.
"""
import os

from .ecs import code_signature, ecs_base


def _is_disabled(value) -> bool:
    # The artifact emits a real boolean ``Disabled`` (from the disposition token).
    # Guard the string forms too — a bare ``bool("[disabled, …]")``/``bool("false")``
    # is always True (the same coercion trap the TCC normalizer hit), so a leaked
    # disposition string must be inspected, not coerced.
    if isinstance(value, str):
        v = value.strip().lower()
        return "disabled" in v or v in ("true", "1", "yes")
    return bool(value)


def normalize_btm(rows: list[dict], host: dict) -> list[dict]:
    """Accepts both the synthetic fixture columns and the custom-VQL output
    (``sfltool dumpbtm``): ``Path``/``Executable``, ``ItemName``/``Name``,
    ``DeveloperName``/``Developer``, ``Disabled`` (inverse of ``Enabled``), and a
    ``Hash``. See profile/custom-vql/MacOS.Raptorscope.BTM.yaml.
    """
    docs = []
    for r in rows:
        executable = r.get("Executable") or r.get("Path") or ""
        # Real dumpbtm carries `Disabled`; the fixture carries `Enabled`.
        if r.get("Disabled") is not None:
            enabled = not _is_disabled(r.get("Disabled"))
        else:
            enabled = bool(r.get("Enabled"))

        doc = ecs_base(host, "macos.persistence")
        doc["@timestamp"] = r.get("Mtime") or ""
        if executable:
            doc["file"] = {"path": executable, "name": os.path.basename(executable)}
            process = {"executable": executable, "command_line": executable}
            sig = code_signature(r.get("CodeSignature"))
            if sig is not None:
                process["code_signature"] = sig
            doc["process"] = process
        persistence = {
            "type": "btm",
            "label": r.get("Name") or r.get("ItemName"),
            "run_at_load": enabled,
            "btm_type": r.get("Type"),
            "developer": r.get("Developer") or r.get("DeveloperName"),
            "uuid": r.get("UUID"),
        }
        if r.get("Hash"):
            h = r["Hash"]
            persistence["hash"] = h.get("SHA256") if isinstance(h, dict) else str(h)
        doc["raptorscope"] = {
            "persistence": persistence,
            "time": {"source": "mtime"},
        }
        docs.append(doc)
    return docs
