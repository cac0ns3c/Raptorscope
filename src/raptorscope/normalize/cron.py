# SPDX-License-Identifier: GPL-3.0-or-later
"""Normalize the Velociraptor macOS crontab/periodic artifact to ECS.

Cron and periodic jobs are a persistence technique; they share the
``macos.persistence`` dataset, discriminated by
``raptorscope.persistence.type = cron``. Source columns confirmed against
``fixtures/velociraptor/cron_items.raw.json``.
"""
import os

from .ecs import ecs_base


def normalize_cron(rows: list[dict], host: dict) -> list[dict]:
    docs = []
    for r in rows:
        path = r.get("Path") or ""
        command = r.get("Command") or ""

        doc = ecs_base(host, "macos.persistence")
        doc["@timestamp"] = r.get("Mtime") or ""
        doc["file"] = {"path": path, "name": os.path.basename(path)}
        if r.get("User"):
            doc["user"] = {"name": r.get("User")}
        if command:
            doc["process"] = {
                "executable": command.split()[0] if command.split() else command,
                "command_line": command,
            }
        doc["raptorscope"] = {
            "persistence": {
                "type": "cron",
                "label": r.get("Path"),
                "run_at_load": False,
                "schedule": r.get("Schedule"),
            }
        }
        docs.append(doc)
    return docs
