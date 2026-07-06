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
    """Accepts both the synthetic fixture columns and the custom-VQL output
    (``profiles show -output stdout-xml``): ``ProfileIdentifier``/
    ``PayloadIdentifier``, ``InstallDate``/``Mtime``, ``PayloadType``, and a boolean
    ``Signed`` (from the profile's verification state). The legacy on-disk source
    also carried ``OSPath``/``SignerCN``. See
    profile/custom-vql/MacOS.Raptorscope.ConfigProfiles.yaml.
    """
    docs = []
    for r in rows:
        path = r.get("OSPath") or r.get("Path") or ""
        signer = r.get("SignerCN")
        # Real custom-VQL emits a boolean `Signed`; the fixture carries `SignerCN`.
        signed = r.get("Signed") if r.get("Signed") is not None else signer is not None

        doc = ecs_base(host, "macos.persistence")
        doc["@timestamp"] = r.get("InstallDate") or r.get("Mtime") or ""
        doc["file"] = {"path": path, "name": os.path.basename(path)}
        if signer is not None:
            doc["process"] = {
                "code_signature": {"subject_name": signer, "trusted": True}
            }
        doc["raptorscope"] = {
            "persistence": {
                "type": "config_profile",
                "label": r.get("ProfileIdentifier") or r.get("PayloadIdentifier"),
                "run_at_load": True,
                "payload_type": r.get("PayloadType"),
                "signed": bool(signed),
            },
            # InstallDate is a true event time; Mtime is file-modified provenance.
            "time": {"source": "event" if r.get("InstallDate") else "mtime"},
        }
        docs.append(doc)
    return docs
