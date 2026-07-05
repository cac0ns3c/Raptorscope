# SPDX-License-Identifier: GPL-3.0-or-later
"""Normalize host network connections (Velociraptor netstat) to ECS.

Dataset ``macos.network``. netstat is a point-in-time socket table, not an event
stream, so ``@timestamp`` is the collection time and provenance is stamped
``raptorscope.time.source = "collection"`` (a snapshot misses short-lived flows).
Source columns: Pid, Name, Family, Type, Status, LocalIP, LocalPort, RemoteIP,
RemotePort (see ``fixtures/velociraptor/network.raw.json``).
"""
from .ecs import ecs_base

_LOOPBACK = ("127.", "::1", "0.0.0.0", "::")


def normalize_network(rows: list[dict], host: dict) -> list[dict]:
    docs = []
    for r in rows:
        state = (r.get("Status") or "").upper()
        rip = r.get("RemoteIP") or ""
        doc = ecs_base(host, "macos.network", category=["network"], type_=["connection"])
        doc["@timestamp"] = r.get("Timestamp") or ""
        net = {"type": "ipv6" if "6" in str(r.get("Family") or "") else "ipv4"}
        if r.get("Type"):
            net["transport"] = str(r.get("Type")).lower()
        if r.get("LocalIP") is not None:
            doc["source"] = {"ip": r.get("LocalIP"), "port": r.get("LocalPort")}
        if rip:
            doc["destination"] = {"ip": rip, "address": rip, "port": r.get("RemotePort")}
        # Direction: a listener is inbound-facing; an established socket with a
        # non-loopback peer is outbound; loopback/no-peer is host-internal.
        if state == "LISTEN":
            net["direction"] = "ingress"
        elif rip and not rip.startswith(_LOOPBACK):
            net["direction"] = "egress"
        else:
            net["direction"] = "internal"
        doc["network"] = net
        if r.get("Pid") is not None:
            doc["process"] = {"pid": r.get("Pid"), "name": r.get("Name")}
        doc["raptorscope"] = {"time": {"source": "collection"}, "network": {"state": state}}
        docs.append(doc)
    return docs
