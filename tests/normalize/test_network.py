# SPDX-License-Identifier: GPL-3.0-or-later
"""normalize_network: field mapping + direction derivation + provenance."""
from raptorscope.normalize.network import normalize_network

HOST = {"name": "h", "os": {"type": "macos"}}


def _one(row):
    return normalize_network([row], HOST)[0]


def test_listener_is_ingress_with_source_port():
    d = _one({"Pid": 6120, "Name": "bash", "Family": "INET", "Type": "TCP",
              "Status": "LISTEN", "LocalIP": "0.0.0.0", "LocalPort": 4444})
    assert d["event"]["dataset"] == "macos.network"
    assert d["network"]["direction"] == "ingress"
    assert d["raptorscope"]["network"]["state"] == "LISTEN"
    assert d["source"]["port"] == 4444
    assert "destination" not in d
    assert d["process"] == {"pid": 6120, "name": "bash"}


def test_established_remote_is_egress_with_destination():
    d = _one({"Pid": 6144, "Name": "bash", "Family": "INET", "Type": "TCP",
              "Status": "ESTABLISHED", "LocalIP": "192.168.1.24", "LocalPort": 51100,
              "RemoteIP": "45.9.148.99", "RemotePort": 443})
    assert d["network"]["direction"] == "egress"
    assert d["destination"] == {"ip": "45.9.148.99", "address": "45.9.148.99", "port": 443}


def test_loopback_peer_is_internal():
    d = _one({"Pid": 500, "Name": "foo", "Family": "INET", "Type": "TCP",
              "Status": "ESTABLISHED", "LocalIP": "127.0.0.1", "LocalPort": 5000,
              "RemoteIP": "127.0.0.1", "RemotePort": 6000})
    assert d["network"]["direction"] == "internal"


def test_provenance_is_collection_time():
    d = _one({"Pid": 1, "Name": "launchd", "Family": "INET", "Type": "TCP",
              "Status": "LISTEN", "LocalIP": "0.0.0.0", "LocalPort": 22})
    assert d["raptorscope"]["time"]["source"] == "collection"


def test_ipv6_family():
    d = _one({"Pid": 1, "Name": "x", "Family": "INET6", "Type": "TCP",
              "Status": "LISTEN", "LocalIP": "::", "LocalPort": 22})
    assert d["network"]["type"] == "ipv6"
