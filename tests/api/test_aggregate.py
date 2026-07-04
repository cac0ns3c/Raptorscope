# SPDX-License-Identifier: GPL-3.0-or-later
"""Store.aggregate returns the overview building blocks (backend-agnostic)."""
from raptorscope.api.store import InMemoryStore
from tests.api.conftest import seed_docs


def test_aggregate_matches_manual_counts():
    store = InMemoryStore(seed_docs())
    agg = store.aggregate(host="mac-victim")
    # dataset counts sum to the host's doc total
    assert sum(agg["datasets"].values()) == store.count(host="mac-victim")
    # persistence types only tally persistence docs
    assert sum(agg["persistence_types"].values()) == store.count(
        host="mac-victim", dataset="macos.persistence"
    )
    assert set(agg["unsigned"]) == {"process", "inventory"}
    assert agg["unsigned"]["process"] >= 1  # the dirty sample has an unsigned proc


def test_overview_endpoint_uses_aggregate(client):
    ov = client.get("/cases/mac-victim/overview").json()
    assert ov["total"] > 0
    assert ov["datasets"]
    assert set(ov["unsigned"]) == {"process", "inventory"}
