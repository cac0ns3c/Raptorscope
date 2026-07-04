# SPDX-License-Identifier: GPL-3.0-or-later
"""Production ``Store`` backed by a live Elasticsearch over ``raptorscope-*``.

Mirrors :class:`raptorscope.api.store.InMemoryStore`: every ``search``/``get``
result is the ECS ``_source`` with the document ``_id`` injected, so the API
layer is identical regardless of backend.
"""
from ..api.store import _INDICATOR_FIELDS, decode_cursor, encode_cursor
from .template import INDEX_PATTERN


def _hit(hit: dict) -> dict:
    src = dict(hit.get("_source") or {})
    src["_id"] = hit.get("_id")
    return src


class ESStore:
    def __init__(self, client, index_pattern: str = INDEX_PATTERN):
        self._client = client
        self._pattern = index_pattern

    def _filter(self, host, dataset) -> list:
        clauses = []
        if host is not None:
            clauses.append({"term": {"host.name": host}})
        if dataset is not None:
            clauses.append({"term": {"event.dataset": dataset}})
        return clauses

    def _terms(self, field: str, host=None) -> list[str]:
        body = {
            "size": 0,
            "query": {"bool": {"filter": self._filter(host, None)}},
            "aggs": {"vals": {"terms": {"field": field, "size": 10000}}},
        }
        resp = self._client.search(index=self._pattern, body=body)
        buckets = resp["aggregations"]["vals"]["buckets"]
        return sorted(b["key"] for b in buckets)

    def hosts(self) -> list[str]:
        return self._terms("host.name")

    def datasets(self, host: str | None = None) -> list[str]:
        return self._terms("event.dataset", host=host)

    def count(self, host: str | None = None, dataset: str | None = None) -> int:
        body = {"query": {"bool": {"filter": self._filter(host, dataset)}}}
        return self._client.count(index=self._pattern, body=body)["count"]

    def aggregate(self, host: str | None = None) -> dict:
        """Overview building blocks via ES aggregations — no full-doc scan."""
        body = {
            "size": 0,
            "query": {"bool": {"filter": self._filter(host, None)}},
            "aggs": {
                "datasets": {"terms": {"field": "event.dataset", "size": 100}},
                "ptypes": {
                    "filter": {"term": {"event.dataset": "macos.persistence"}},
                    "aggs": {
                        "vals": {
                            "terms": {
                                "field": "raptorscope.persistence.type",
                                "size": 100,
                            }
                        }
                    },
                },
                "unsigned_process": {
                    "filter": {
                        "bool": {
                            "filter": [{"term": {"event.dataset": "macos.process"}}],
                            "must_not": [
                                {"term": {"process.code_signature.trusted": True}}
                            ],
                        }
                    }
                },
                "unsigned_inventory": {
                    "filter": {
                        "bool": {
                            "filter": [
                                {"term": {"event.dataset": "macos.inventory"}},
                                {"term": {"raptorscope.app.signed": False}},
                            ]
                        }
                    }
                },
            },
        }
        aggs = self._client.search(index=self._pattern, body=body)["aggregations"]
        return {
            "datasets": {
                b["key"]: b["doc_count"] for b in aggs["datasets"]["buckets"]
            },
            "persistence_types": {
                b["key"]: b["doc_count"]
                for b in aggs["ptypes"]["vals"]["buckets"]
            },
            "unsigned": {
                "process": aggs["unsigned_process"]["doc_count"],
                "inventory": aggs["unsigned_inventory"]["doc_count"],
            },
        }

    # ES rejects ``from + size`` above ``index.max_result_window`` (default 10k).
    # A single collected host is far under that, so we cap at the window rather
    # than carry PIT/scroll machinery. (Raise the setting + revisit if needed.)
    MAX_WINDOW = 10000

    def search(
        self,
        host: str | None = None,
        dataset: str | None = None,
        size: int = 1000,
        sort: tuple[str, str] | None = None,
        offset: int = 0,
    ) -> list[dict]:
        # ES rejects ``from + size`` past ``index.max_result_window`` (10k). For a
        # single collected host that's ample; paging beyond it needs PIT +
        # search_after (tracked as the deep-pagination follow-up).
        size = min(size, self.MAX_WINDOW)
        if offset + size > self.MAX_WINDOW:
            offset = max(0, self.MAX_WINDOW - size)
        body: dict = {
            "from": offset,
            "size": size,
            "query": {"bool": {"filter": self._filter(host, dataset)}},
        }
        if sort is not None:
            field, order = sort
            body["sort"] = [{field: {"order": order}}]
        resp = self._client.search(index=self._pattern, body=body)
        return [_hit(h) for h in resp["hits"]["hits"]]

    def hunt(self, value: str, size: int = 100) -> list[dict]:
        """Cross-host IOC correlation: substring-match ``value`` across the
        indicator fields (all keyword/`wildcard` typed) over the whole fleet."""
        should = [
            {"wildcard": {f: {"value": f"*{value}*"}}} for f in _INDICATOR_FIELDS
        ]
        body = {
            "size": min(size, self.MAX_WINDOW),
            "query": {"bool": {"should": should, "minimum_should_match": 1}},
        }
        resp = self._client.search(index=self._pattern, body=body)
        return [_hit(h) for h in resp["hits"]["hits"]]

    def page(
        self,
        host: str | None = None,
        dataset: str | None = None,
        size: int = 50,
        cursor: str | None = None,
        sort_field: str = "@timestamp",
        order: str = "asc",
    ) -> dict:
        """Deep pagination past the 10k window via Point-in-Time + search_after.

        Returns ``{items, cursor}``; pass the cursor back for the next page. The
        cursor carries the PIT id and the last sort values. The PIT is closed when
        the final (short) page is reached.
        """
        size = min(size, self.MAX_WINDOW)
        pit_id = after = None
        if cursor:
            st = decode_cursor(cursor)
            pit_id, after = st.get("pit"), st.get("after")
        if pit_id is None:
            pit_id = self._client.open_point_in_time(
                index=self._pattern, keep_alive="1m"
            )["id"]
        body: dict = {
            "size": size,
            "query": {"bool": {"filter": self._filter(host, dataset)}},
            "pit": {"id": pit_id, "keep_alive": "1m"},
            # A tiebreaker (`_shard_doc`, PIT-only) makes the ordering total/stable.
            "sort": [{sort_field: {"order": order}}, {"_shard_doc": "asc"}],
        }
        if after is not None:
            body["search_after"] = after
        resp = self._client.search(body=body)  # PIT carries the index — omit it
        pit_id = resp.get("pit_id", pit_id)
        hits = resp["hits"]["hits"]
        items = [_hit(h) for h in hits]
        if len(hits) < size:  # last page — release the PIT
            try:
                self._client.close_point_in_time(id=pit_id)
            except Exception:  # noqa: BLE001 - best-effort cleanup
                pass
            return {"items": items, "cursor": None}
        return {
            "items": items,
            "cursor": encode_cursor({"pit": pit_id, "after": hits[-1]["sort"]}),
        }

    def get(self, doc_id: str) -> dict | None:
        body = {"size": 1, "query": {"ids": {"values": [doc_id]}}}
        hits = self._client.search(index=self._pattern, body=body)["hits"]["hits"]
        return _hit(hits[0]) if hits else None
