# SPDX-License-Identifier: GPL-3.0-or-later
"""Normalize the Velociraptor macOS installed-applications inventory to ECS.

Dataset ``macos.inventory`` (``event.category = ["package"]``). Source columns
confirmed against ``fixtures/velociraptor/installed_apps.raw.json``.
"""
import os

from .ecs import ecs_base


def normalize_inventory(rows: list[dict], host: dict) -> list[dict]:
    docs = []
    for r in rows:
        path = r.get("Path") or ""
        signer = r.get("SignerCN")

        doc = ecs_base(host, "macos.inventory", category=["package"], type_=["info"])
        doc["@timestamp"] = r.get("Mtime") or ""
        doc["file"] = {"path": path, "name": os.path.basename(path)}
        if signer is not None:
            doc["process"] = {
                "code_signature": {"subject_name": signer, "trusted": True}
            }
        doc["raptorscope"] = {
            "app": {
                "name": r.get("Name"),
                "bundle_id": r.get("BundleIdentifier"),
                "version": r.get("Version"),
                "signed": signer is not None,
            }
        }
        docs.append(doc)
    return docs
