# SPDX-License-Identifier: GPL-3.0-or-later
"""Datastore abstraction for the API.

The API talks only to this ``Store`` interface, so contract tests run against an
``InMemoryStore`` seeded from fixtures while production uses ``ESStore``
(``raptorscope.es.store``) over a live Elasticsearch. Every method returns the
same ECS docs the normalizers emit; ``search``/``get`` results carry an injected
``_id`` for pivot-to-evidence.
"""
from typing import Protocol, runtime_checkable


def _host_of(doc: dict) -> str | None:
    return (doc.get("host") or {}).get("name")


def _dataset_of(doc: dict) -> str | None:
    return (doc.get("event") or {}).get("dataset")


@runtime_checkable
class Store(Protocol):
    def hosts(self) -> list[str]: ...

    def datasets(self, host: str | None = None) -> list[str]: ...

    def count(self, host: str | None = None, dataset: str | None = None) -> int: ...

    def search(
        self,
        host: str | None = None,
        dataset: str | None = None,
        size: int = 1000,
        sort: tuple[str, str] | None = None,
    ) -> list[dict]: ...

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

    def search(
        self,
        host: str | None = None,
        dataset: str | None = None,
        size: int = 1000,
        sort: tuple[str, str] | None = None,
    ) -> list[dict]:
        hits = [d for d in self._docs if self._match(d, host, dataset)]
        if sort is not None:
            field, order = sort
            hits.sort(key=lambda d: d.get(field) or "", reverse=(order == "desc"))
        return hits[:size]

    def get(self, doc_id: str) -> dict | None:
        return self._by_id.get(doc_id)
