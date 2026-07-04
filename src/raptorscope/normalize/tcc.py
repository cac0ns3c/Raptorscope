# SPDX-License-Identifier: GPL-3.0-or-later
"""Normalize the Velociraptor macOS TCC.db artifact to ECS.

TCC.db records privacy authorizations (camera, mic, accessibility, full-disk,
input-monitoring, …). Dataset ``macos.tcc``. Source columns confirmed against
``fixtures/velociraptor/tcc.raw.json``.

``ClientType``: 0 = bundle identifier, 1 = absolute path. ``AuthValue``: 2 =
allowed, 0 = denied (3 = limited on newer macOS, treated as allowed).
"""
import os

from .ecs import ecs_base


def normalize_tcc(rows: list[dict], host: dict) -> list[dict]:
    docs = []
    for r in rows:
        path = r.get("Path") or ""
        client = r.get("Client")
        client_type = r.get("ClientType")
        # Real MacOS.System.TCC emits a boolean ``Allowed``; the synthetic fixture
        # uses the raw ``AuthValue`` (2 = allowed).
        if "Allowed" in r:
            allowed = bool(r.get("Allowed"))
        else:
            allowed = int(r.get("AuthValue") or 0) >= 2

        doc = ecs_base(host, "macos.tcc")
        doc["@timestamp"] = r.get("LastModified") or ""
        if path:
            doc["file"] = {"path": path, "name": os.path.basename(path)}
        # ClientType 1 means Client is an absolute executable path.
        if client and client_type == 1:
            doc["process"] = {"executable": client}
        doc["raptorscope"] = {
            "tcc": {
                "service": r.get("Service"),
                "client": client,
                "client_type": "path" if client_type == 1 else "bundle_id",
                "allowed": allowed,
            }
        }
        docs.append(doc)
    return docs
