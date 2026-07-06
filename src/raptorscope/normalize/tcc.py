# SPDX-License-Identifier: GPL-3.0-or-later
"""Normalize the Velociraptor macOS TCC.db artifact to ECS.

TCC.db records privacy authorizations (camera, mic, accessibility, full-disk,
input-monitoring, …). Dataset ``macos.tcc``. Source columns confirmed against
``fixtures/velociraptor/tcc.raw.json``.

The real ``MacOS.System.TCC`` built-in emits **string** encodings (validated on
real data 2026-07-05): ``ClientType`` is ``"Console"`` (bundle id, raw
client_type 0) / ``"Service/Script"`` (absolute path, raw 1) / ``"Other"``, and
``Allowed`` is ``"Yes"``/``"No"`` (from ``if(auth_value=2,"Yes","No")``). The
synthetic fixture instead carries the raw ints ``ClientType`` 0/1 and
``AuthValue`` 2. Both shapes are handled below.
"""
import os

from .ecs import ecs_base

# ClientType values (string form from the built-in, int form from the fixture)
# that mean ``Client`` is an absolute executable path rather than a bundle id.
_PATH_CLIENT_TYPES = {1, "Service/Script"}


def _is_allowed(r: dict) -> bool:
    # Real data: ``Allowed`` is the string "Yes"/"No" — note ``bool("No")`` is
    # True, so it MUST be compared, not coerced. Fixture: raw ``AuthValue`` int.
    if "Allowed" in r:
        a = r.get("Allowed")
        if isinstance(a, str):
            return a.strip().lower() in ("yes", "true", "1")
        return bool(a)
    return int(r.get("AuthValue") or 0) >= 2


def normalize_tcc(rows: list[dict], host: dict) -> list[dict]:
    docs = []
    for r in rows:
        # Fixture carries the source TCC.db path as ``Path``; the real built-in
        # exposes it as ``_OSPath``.
        path = r.get("Path") or r.get("_OSPath") or ""
        client = r.get("Client")
        client_type = r.get("ClientType")
        is_path_client = client_type in _PATH_CLIENT_TYPES
        allowed = _is_allowed(r)

        doc = ecs_base(host, "macos.tcc")
        doc["@timestamp"] = r.get("LastModified") or ""
        if path:
            doc["file"] = {"path": path, "name": os.path.basename(path)}
        if client and is_path_client:
            doc["process"] = {"executable": client}
        doc["raptorscope"] = {
            "tcc": {
                "service": r.get("Service"),
                "client": client,
                "client_type": "path" if is_path_client else "bundle_id",
                "allowed": allowed,
            }
        }
        docs.append(doc)
    return docs
