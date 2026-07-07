# SPDX-License-Identifier: GPL-3.0-or-later
"""Server-side triage state: shared, persisted, actor-stamped (panel-review fix #3)."""


def test_triage_roundtrip_and_actor(client):
    # empty to start
    assert client.get("/cases/mac-victim/triage").json() == {}
    # set an ack
    r = client.post(
        "/cases/mac-victim/triage",
        json={"rule_id": "r1", "doc_id": "d1", "status": "ack"},
    )
    assert r.status_code == 200
    entry = r.json()
    assert entry["status"] == "ack"
    assert entry["actor"] == "-"  # no auth in this fixture
    assert entry["ts"]
    # a second client (== another analyst on the same server) sees it
    got = client.get("/cases/mac-victim/triage").json()
    assert got["r1|d1"]["status"] == "ack"


def test_triage_note_and_clear(client):
    client.post(
        "/cases/mac-victim/triage",
        json={"rule_id": "r2", "doc_id": "d2", "note": "looks real"},
    )
    got = client.get("/cases/mac-victim/triage").json()
    assert got["r2|d2"]["note"] == "looks real"
    # clearing status+note removes the entry entirely
    client.post(
        "/cases/mac-victim/triage",
        json={"rule_id": "r2", "doc_id": "d2", "note": ""},
    )
    assert "r2|d2" not in client.get("/cases/mac-victim/triage").json()


def test_doc_ids_are_content_stable_across_reingest():
    # Re-building the store from the same docs yields identical ids (a triage key
    # attached to a doc survives re-ingest, unlike an enumeration index).
    from raptorscope.api.store import InMemoryStore

    docs = [
        {"event": {"dataset": "macos.tcc"}, "raptorscope": {"tcc": {"service": "x"}}},
        {"event": {"dataset": "macos.process"}, "process": {"pid": 5}},
    ]
    ids1 = [d["_id"] for d in InMemoryStore([dict(x) for x in docs])._docs]
    # re-ingest with an extra doc prepended (would reshuffle enumeration indices)
    docs2 = [{"event": {"dataset": "macos.network"}}] + docs
    by_id = {d["_id"]: d for d in InMemoryStore([dict(x) for x in docs2])._docs}
    # the original two docs keep their ids despite the new doc shifting positions
    for i in ids1:
        assert i in by_id
