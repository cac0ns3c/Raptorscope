# SPDX-License-Identifier: GPL-3.0-or-later
"""Normalize the Velociraptor macOS running-process listing to ECS.

Dataset ``macos.process`` (``event.category = ["process"]``). Source columns
confirmed against ``fixtures/velociraptor/processes.raw.json``.
"""
import os

from .ecs import code_signature, ecs_base


def normalize_processes(rows: list[dict], host: dict) -> list[dict]:
    docs = []
    for r in rows:
        exe = r.get("Exe") or ""

        doc = ecs_base(host, "macos.process", category=["process"], type_=["info"])
        # Mtime = synthetic; real MacOS.Sys.Pslist emits `CreateTime` (verified
        # against a live capture), older/Linux variants `CreatedTime`.
        doc["@timestamp"] = (
            r.get("Mtime") or r.get("CreateTime") or r.get("CreatedTime") or ""
        )
        if exe:
            doc["file"] = {"path": exe, "name": os.path.basename(exe)}

        process: dict = {
            "name": r.get("Name"),
            "executable": exe or None,
            "command_line": r.get("CommandLine") or exe or None,
        }
        if r.get("Pid") is not None:
            process["pid"] = r.get("Pid")
        if r.get("Ppid") is not None:
            process["parent"] = {"pid": r.get("Ppid")}
        sig = code_signature(r.get("CodeSignature"))
        if sig is not None:
            process["code_signature"] = sig
        doc["process"] = process

        if r.get("Username"):
            doc["user"] = {"name": r.get("Username")}
        docs.append(doc)
    return docs
