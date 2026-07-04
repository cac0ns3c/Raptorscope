# SPDX-License-Identifier: GPL-3.0-or-later
"""Normalize the Velociraptor macOS configuration/MDM profiles artifact to ECS.

Installed profiles are a persistence/config-manipulation technique; they share
the ``macos.persistence`` dataset, discriminated by
``raptorscope.persistence.type = config_profile``. Source columns confirmed
against ``fixtures/velociraptor/config_profiles.raw.json``.
"""
import os

from .ecs import ecs_base


def normalize_config_profiles(rows: list[dict], host: dict) -> list[dict]:
    docs = []
    for r in rows:
        path = r.get("Path") or ""
        signer = r.get("SignerCN")

        doc = ecs_base(host, "macos.persistence")
        doc["@timestamp"] = r.get("InstallDate") or ""
        doc["file"] = {"path": path, "name": os.path.basename(path)}
        if signer is not None:
            doc["process"] = {
                "code_signature": {"subject_name": signer, "trusted": True}
            }
        doc["raptorscope"] = {
            "persistence": {
                "type": "config_profile",
                "label": r.get("ProfileIdentifier"),
                "run_at_load": True,
                "payload_type": r.get("PayloadType"),
                "signed": signer is not None,
            }
        }
        docs.append(doc)
    return docs
