# SPDX-License-Identifier: GPL-3.0-or-later
"""Normalize the Velociraptor macOS LSQuarantine artifact to ECS.

The QuarantineEventsV2 database records files downloaded via quarantine-aware
apps: what was downloaded, from where, and by which agent. Dataset
``macos.quarantine`` (``event.category = ["file"]``, ``type = ["creation"]``).
Source columns confirmed against ``fixtures/velociraptor/quarantine.raw.json``.
"""
import os

from .ecs import ecs_base


def normalize_quarantine(rows: list[dict], host: dict) -> list[dict]:
    docs = []
    for r in rows:
        path = r.get("Path") or ""

        doc = ecs_base(host, "macos.quarantine", category=["file"], type_=["creation"])
        doc["@timestamp"] = r.get("LSQuarantineTimeStamp") or ""
        doc["file"] = {"path": path, "name": os.path.basename(path)}

        url: dict = {}
        if r.get("LSQuarantineDataURLString"):
            url["full"] = r.get("LSQuarantineDataURLString")
        if r.get("LSQuarantineOriginURLString"):
            url["original"] = r.get("LSQuarantineOriginURLString")
        if url:
            doc["url"] = url

        if r.get("LSQuarantineAgentName"):
            doc["process"] = {"name": r.get("LSQuarantineAgentName")}

        doc["raptorscope"] = {
            "quarantine": {"sender": r.get("LSQuarantineSenderName")}
        }
        docs.append(doc)
    return docs
