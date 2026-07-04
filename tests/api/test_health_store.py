# SPDX-License-Identifier: GPL-3.0-or-later
from raptorscope.api.store import InMemoryStore


def test_health_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_store_filters_by_host_and_dataset(store):
    from tests.api.conftest import DIRTY_HOST, DIRTY_DOC_COUNT

    assert set(store.hosts()) == {"mac-victim", "mac-clean"}
    assert store.count(host=DIRTY_HOST) == DIRTY_DOC_COUNT
    persistence = store.search(host=DIRTY_HOST, dataset="macos.persistence")
    assert persistence
    assert all(d["event"]["dataset"] == "macos.persistence" for d in persistence)
    assert all(d["host"]["name"] == DIRTY_HOST for d in persistence)


def test_store_get_by_id_roundtrip(store):
    doc = store.search(host="mac-victim", dataset="macos.tcc")[0]
    assert store.get(doc["_id"])["_id"] == doc["_id"]


def test_empty_store_has_no_hosts():
    s = InMemoryStore([])
    assert s.hosts() == []
    assert s.count() == 0
