# SPDX-License-Identifier: GPL-3.0-or-later
"""Production ``Store`` backed by a live Elasticsearch over ``raptorscope-*``.

Mirrors :class:`raptorscope.api.store.InMemoryStore`: every ``search``/``get``
result is the ECS ``_source`` with the document ``_id`` injected, so the API
layer is identical regardless of backend.
"""
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

    def search(
        self,
        host: str | None = None,
        dataset: str | None = None,
        size: int = 1000,
        sort: tuple[str, str] | None = None,
    ) -> list[dict]:
        body = {
            "size": size,
            "query": {"bool": {"filter": self._filter(host, dataset)}},
        }
        if sort is not None:
            field, order = sort
            body["sort"] = [{field: {"order": order}}]
        resp = self._client.search(index=self._pattern, body=body)
        return [_hit(h) for h in resp["hits"]["hits"]]

    def get(self, doc_id: str) -> dict | None:
        body = {"size": 1, "query": {"ids": {"values": [doc_id]}}}
        hits = self._client.search(index=self._pattern, body=body)["hits"]["hits"]
        return _hit(hits[0]) if hits else None
