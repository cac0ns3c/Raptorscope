# SPDX-License-Identifier: GPL-3.0-or-later
"""Regressions for the code-review findings: throttled 429s stay observable, and
InMemoryStore.page mirrors ESStore's @timestamp ordering."""
from fastapi.testclient import TestClient

from raptorscope.api.app import create_app
from raptorscope.api.store import InMemoryStore
from tests.api.test_ai import FakeAI, seed_docs


def test_rate_limited_429_is_still_observed():
    # 429 must pass back through the access-log/audit/metrics middleware, so the
    # abuse it throttles is not invisible. X-Request-ID proves it did.
    c = TestClient(create_app(InMemoryStore(seed_docs()), ai=FakeAI(), ai_rate=1))
    assert c.post("/cases/mac-victim/ai/summary").status_code == 200
    r = c.post("/cases/mac-victim/ai/summary")
    assert r.status_code == 429
    assert "x-request-id" in {k.lower() for k in r.headers}
    # and it was counted in /metrics (status bucketed into the 4xx class)
    assert 'class="4xx"' in c.get("/metrics").text


def test_inmemory_page_orders_by_timestamp_like_es():
    # docs inserted NEWEST-first; page() must return @timestamp-ascending regardless
    docs = [
        {"@timestamp": "2026-07-03T00:00:03Z", "event": {"dataset": "macos.process"},
         "host": {"name": "h"}, "process": {"pid": 3}},
        {"@timestamp": "2026-07-03T00:00:01Z", "event": {"dataset": "macos.process"},
         "host": {"name": "h"}, "process": {"pid": 1}},
        {"@timestamp": "2026-07-03T00:00:02Z", "event": {"dataset": "macos.process"},
         "host": {"name": "h"}, "process": {"pid": 2}},
    ]
    store = InMemoryStore(docs)
    page = store.page(host="h", dataset="macos.process", size=2)
    got = [d["@timestamp"] for d in page["items"]]
    assert got == ["2026-07-03T00:00:01Z", "2026-07-03T00:00:02Z"]


def test_search_default_sort_is_deterministic_and_pages_are_disjoint():
    # docs inserted out of order; search() with no explicit sort must be
    # @timestamp-ascending, so offset windows don't overlap or drop rows.
    docs = [
        {"@timestamp": f"2026-07-03T00:00:0{9 - i}Z",
         "event": {"dataset": "macos.process"}, "host": {"name": "h"},
         "process": {"pid": i}}
        for i in range(6)
    ]
    store = InMemoryStore(docs)
    ts = [d["@timestamp"] for d in store.search(host="h", dataset="macos.process")]
    assert ts == sorted(ts)  # ascending, deterministic
    first = store.search(host="h", dataset="macos.process", size=3, offset=0)
    second = store.search(host="h", dataset="macos.process", size=3, offset=3)
    ids = [d["_id"] for d in first] + [d["_id"] for d in second]
    assert len(set(ids)) == 6  # disjoint, full coverage
