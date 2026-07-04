# SPDX-License-Identifier: GPL-3.0-or-later
"""Normalize the Velociraptor macOS installed-applications inventory to ECS.

Dataset ``macos.inventory`` (``event.category = ["package"]``). Accepts both the
synthetic fixture columns and the **real** ``MacOS.System.Packages`` columns
(``SignedBy``/``LastModified``; see the real-Velociraptor validation spike note).
"""
import os

from .ecs import ecs_base

# Signature strings the real MacOS.System.Packages artifact uses for unsigned apps.
_UNSIGNED = {None, "", "Unsigned", "unsigned", "Not signed", "None"}


def normalize_inventory(rows: list[dict], host: dict) -> list[dict]:
    docs = []
    for r in rows:
        path = r.get("Path") or ""
        # SignerCN = synthetic; SignedBy = real MacOS.System.Packages.
        signer = r.get("SignerCN") or r.get("SignedBy")
        signed = signer not in _UNSIGNED

        doc = ecs_base(host, "macos.inventory", category=["package"], type_=["info"])
        doc["@timestamp"] = r.get("Mtime") or r.get("LastModified") or ""
        doc["file"] = {"path": path, "name": os.path.basename(path)}
        if signed:
            doc["process"] = {
                "code_signature": {"subject_name": signer, "trusted": True}
            }
        doc["raptorscope"] = {
            "app": {
                "name": r.get("Name"),
                "bundle_id": r.get("BundleIdentifier"),
                "version": r.get("Version"),
                "obtained_from": r.get("ObtainedFrom"),
                "signed": signed,
            }
        }
        docs.append(doc)
    return docs
