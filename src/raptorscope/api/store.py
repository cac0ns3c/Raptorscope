# SPDX-License-Identifier: GPL-3.0-or-later
"""Datastore abstraction for the API.

The API talks only to this ``Store`` interface, so contract tests run against an
``InMemoryStore`` seeded from fixtures while production uses ``ESStore``
(``raptorscope.es.store``) over a live Elasticsearch. Every method returns the
same ECS docs the normalizers emit; ``search``/``get`` results carry an injected
``_id`` for pivot-to-evidence.
"""
import base64
import json
from collections import Counter
from typing import Protocol, runtime_checkable


def encode_cursor(state: dict) -> str:
    return base64.urlsafe_b64encode(json.dumps(state).encode()).decode()


def decode_cursor(cursor: str) -> dict:
    return json.loads(base64.urlsafe_b64decode(cursor.encode()).decode())


def _host_of(doc: dict) -> str | None:
    return (doc.get("host") or {}).get("name")


def _dataset_of(doc: dict) -> str | None:
    return (doc.get("event") or {}).get("dataset")


def _dig(doc: dict, path: str):
    cur = doc
    for key in path.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
    return cur


# Fields an indicator (IP, path, hash, label, client) can appear in — used by the
# cross-host hunt to correlate an IOC across the whole fleet. All are keyword or
# `wildcard`-typed in ES, so substring wildcard queries match the in-memory path.
_INDICATOR_FIELDS = [
    "file.path",
    "process.executable",
    "process.command_line",
    "url.full",
    "url.original",
    "raptorscope.persistence.label",
    "raptorscope.persistence.hash",
    "raptorscope.tcc.client",
    "host.name",
]


@runtime_checkable
class Store(Protocol):
    def hosts(self) -> list[str]: ...

    def datasets(self, host: str | None = None) -> list[str]: ...

    def count(self, host: str | None = None, dataset: str | None = None) -> int: ...

    def aggregate(self, host: str | None = None) -> dict: ...

    def hunt(self, value: str, size: int = 100) -> list[dict]: ...

    def search(
        self,
        host: str | None = None,
        dataset: str | None = None,
        size: int = 1000,
        sort: tuple[str, str] | None = None,
        offset: int = 0,
    ) -> list[dict]: ...

    def page(
        self,
        host: str | None = None,
        dataset: str | None = None,
        size: int = 50,
        cursor: str | None = None,
    ) -> dict: ...

    def get(self, doc_id: str) -> dict | None: ...


class InMemoryStore:
    """A ``Store`` backed by a list of ECS docs held in memory."""

    def __init__(self, docs: list[dict]):
        # Assign a stable id per doc; keep an id->doc index for get().
        self._docs: list[dict] = []
        self._by_id: dict[str, dict] = {}
        for i, src in enumerate(docs):
            doc = dict(src)
            doc["_id"] = str(i)
            self._docs.append(doc)
            self._by_id[doc["_id"]] = doc

    def _match(self, doc, host, dataset) -> bool:
        if host is not None and _host_of(doc) != host:
            return False
        if dataset is not None and _dataset_of(doc) != dataset:
            return False
        return True

    def hosts(self) -> list[str]:
        return sorted({h for d in self._docs if (h := _host_of(d)) is not None})

    def datasets(self, host: str | None = None) -> list[str]:
        return sorted(
            {
                ds
                for d in self._docs
                if self._match(d, host, None) and (ds := _dataset_of(d)) is not None
            }
        )

    def count(self, host: str | None = None, dataset: str | None = None) -> int:
        return sum(1 for d in self._docs if self._match(d, host, dataset))

    def aggregate(self, host: str | None = None) -> dict:
        """Overview building blocks (dataset counts, persistence-type breakdown,
        unsigned tallies) — the in-memory equivalent of the ES aggregations."""
        docs = [d for d in self._docs if self._match(d, host, None)]
        return {
            "datasets": dict(Counter(_dataset_of(d) for d in docs)),
            "persistence_types": dict(
                Counter(
                    _dig(d, "raptorscope.persistence.type")
                    for d in docs
                    if _dataset_of(d) == "macos.persistence"
                )
            ),
            "unsigned": {
                "process": sum(
                    1
                    for d in docs
                    if _dataset_of(d) == "macos.process"
                    and _dig(d, "process.code_signature.trusted") is not True
                ),
                "inventory": sum(
                    1
                    for d in docs
                    if _dataset_of(d) == "macos.inventory"
                    and _dig(d, "raptorscope.app.signed") is False
                ),
            },
        }

    def hunt(self, value: str, size: int = 100) -> list[dict]:
        """Docs across ALL hosts where ``value`` (case-sensitive substring) appears
        in any indicator field — the fleet-wide IOC correlation primitive."""
        hits = []
        for d in self._docs:
            for f in _INDICATOR_FIELDS:
                v = _dig(d, f)
                if v is not None and value in str(v):
                    hits.append(d)
                    break
        return hits[:size]

    def search(
        self,
        host: str | None = None,
        dataset: str | None = None,
        size: int = 1000,
        sort: tuple[str, str] | None = None,
        offset: int = 0,
    ) -> list[dict]:
        hits = [d for d in self._docs if self._match(d, host, dataset)]
        if sort is not None:
            field, order = sort
            hits.sort(key=lambda d: d.get(field) or "", reverse=(order == "desc"))
        return hits[offset : offset + size]

    def page(
        self,
        host: str | None = None,
        dataset: str | None = None,
        size: int = 50,
        cursor: str | None = None,
    ) -> dict:
        """Cursor pagination (in-memory analog of ES PIT + search_after): returns
        ``{items, cursor}`` where a non-null cursor resumes the next page."""
        offset = decode_cursor(cursor).get("offset", 0) if cursor else 0
        hits = [d for d in self._docs if self._match(d, host, dataset)]
        items = hits[offset : offset + size]
        nxt = (
            encode_cursor({"offset": offset + size})
            if offset + size < len(hits)
            else None
        )
        return {"items": items, "cursor": nxt}

    def get(self, doc_id: str) -> dict | None:
        return self._by_id.get(doc_id)
