# SPDX-License-Identifier: GPL-3.0-or-later
"""Deep cursor pagination: in-memory endpoint + ESStore PIT/search_after (fake ES)."""
from fastapi.testclient import TestClient

from raptorscope.api.app import create_app
from raptorscope.api.store import InMemoryStore
from raptorscope.es.store import ESStore


# ---- in-memory cursor traversal via the endpoint ----
def _docs(n, dataset="macos.process"):
    return [
        {
            "host": {"name": "h", "os": {"type": "macos"}},
            "event": {"dataset": dataset},
            "@timestamp": f"2026-07-01T00:00:{i:02d}Z",
            "process": {"pid": i},
        }
        for i in range(n)
    ]


def test_cursor_walks_every_doc_once():
    c = TestClient(create_app(InMemoryStore(_docs(25))))
    seen, cursor, pages = [], "", 0
    while True:
        qs = f"?limit=10{f'&cursor={cursor}' if cursor else ''}"
        body = c.get(f"/cases/h/artifacts/macos.process/page{qs}").json()
        seen += [d["_id"] for d in body["items"]]
        cursor, pages = body["cursor"], pages + 1
        assert pages < 20
        if not cursor:
            break
    # full coverage, no duplicates, correct count
    assert len(seen) == 25
    assert len(set(seen)) == 25


# ---- ESStore.page drives PIT + search_after correctly (fake ES) ----
class FakeES:
    def __init__(self, n):
        # docs sorted ascending by a total order [key, tiebreaker]
        self.docs = [
            {"_id": str(i), "_source": {"event": {"dataset": "macos.process"}},
             "sort": [i, i]}
            for i in range(n)
        ]
        self.opened, self.closed, self._c = [], [], 0

    def open_point_in_time(self, index, keep_alive):
        self._c += 1
        pid = f"pit-{self._c}"
        self.opened.append(pid)
        return {"id": pid}

    def search(self, body=None, index=None):
        after = body.get("search_after")
        docs = self.docs if after is None else [d for d in self.docs if d["sort"] > after]
        page = docs[: body["size"]]
        return {"pit_id": body["pit"]["id"], "hits": {"hits": page}}

    def close_point_in_time(self, id):
        self.closed.append(id)


def test_es_page_pit_search_after_full_walk():
    es = FakeES(25)
    store = ESStore(es)
    seen, cursor, pages = [], None, 0
    while True:
        res = store.page(host="h", dataset="macos.process", size=10, cursor=cursor)
        seen += [d["_id"] for d in res["items"]]
        cursor, pages = res["cursor"], pages + 1
        assert pages < 20
        if cursor is None:
            break
    assert seen == [str(i) for i in range(25)]  # ordered, complete, unique
    assert es.opened == ["pit-1"]  # a single PIT reused across pages
    assert es.closed == ["pit-1"]  # released on the final page


def test_es_page_resumes_from_cursor_pit():
    es = FakeES(25)
    store = ESStore(es)
    first = store.page(host="h", dataset="macos.process", size=10)
    assert first["cursor"]  # more pages
    # the cursor encodes the PIT + search_after; second call reuses the PIT
    second = store.page(host="h", dataset="macos.process", size=10, cursor=first["cursor"])
    assert [d["_id"] for d in second["items"]] == [str(i) for i in range(10, 20)]
    assert es.opened == ["pit-1"]  # no new PIT opened for page 2
