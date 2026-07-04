# SPDX-License-Identifier: GPL-3.0-or-later
"""FastAPI application factory for the raptorscope query API.

``create_app(store)`` wires a :class:`~raptorscope.api.store.Store` into the
routes via closure, so tests build an app around a seeded ``InMemoryStore`` and
production builds one around ``ESStore``. A *case* is a collected host
(``host.name``).
"""
from collections import Counter

from fastapi import FastAPI, HTTPException

from .store import Store


def _dig(doc: dict, path: str):
    cur = doc
    for key in path.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
    return cur


def _summary(doc: dict) -> str:
    """A one-line, dataset-aware description for the timeline."""
    ds = _dig(doc, "event.dataset")
    if ds == "macos.persistence":
        ptype = _dig(doc, "raptorscope.persistence.type")
        label = _dig(doc, "raptorscope.persistence.label")
        return f"{ptype}: {label} ({_dig(doc, 'file.path')})"
    if ds == "macos.process":
        return (
            f"{_dig(doc, 'process.name')} [{_dig(doc, 'process.pid')}] "
            f"{_dig(doc, 'process.executable')}"
        )
    if ds == "macos.quarantine":
        return (
            f"downloaded {_dig(doc, 'file.name')} "
            f"from {_dig(doc, 'url.original')}"
        )
    if ds == "macos.tcc":
        state = "allowed" if _dig(doc, "raptorscope.tcc.allowed") else "denied"
        return (
            f"{_dig(doc, 'raptorscope.tcc.service')} -> "
            f"{_dig(doc, 'raptorscope.tcc.client')} ({state})"
        )
    if ds == "macos.inventory":
        return (
            f"{_dig(doc, 'raptorscope.app.name')} "
            f"{_dig(doc, 'raptorscope.app.version')} ({_dig(doc, 'file.path')})"
        )
    return _dig(doc, "file.path") or ds or ""


def create_app(store: Store) -> FastAPI:
    app = FastAPI(title="Raptorscope API", version="0.1.0")

    def require_case(case: str) -> None:
        if case not in store.hosts():
            raise HTTPException(status_code=404, detail=f"unknown case: {case}")

    def case_summary(case: str) -> dict:
        return {
            "name": case,
            "doc_count": store.count(host=case),
            "datasets": store.datasets(host=case),
        }

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/cases")
    def list_cases():
        return [case_summary(h) for h in store.hosts()]

    @app.get("/cases/{case}")
    def get_case(case: str):
        require_case(case)
        return case_summary(case)

    @app.get("/cases/{case}/overview")
    def overview(case: str):
        require_case(case)
        docs = store.search(host=case, size=100000)
        datasets = Counter(_dig(d, "event.dataset") for d in docs)
        ptypes = Counter(
            _dig(d, "raptorscope.persistence.type")
            for d in docs
            if _dig(d, "event.dataset") == "macos.persistence"
        )
        unsigned_proc = sum(
            1
            for d in docs
            if _dig(d, "event.dataset") == "macos.process"
            and _dig(d, "process.code_signature.trusted") is not True
        )
        unsigned_app = sum(
            1
            for d in docs
            if _dig(d, "event.dataset") == "macos.inventory"
            and _dig(d, "raptorscope.app.signed") is False
        )
        return {
            "case": case,
            "total": len(docs),
            "datasets": dict(datasets),
            "persistence_types": dict(ptypes),
            "unsigned": {"process": unsigned_proc, "inventory": unsigned_app},
        }

    @app.get("/cases/{case}/artifacts/{dataset}")
    def artifact_view(case: str, dataset: str, limit: int = 50, offset: int = 0):
        require_case(case)
        hits = store.search(host=case, dataset=dataset, size=100000)
        return {
            "dataset": dataset,
            "total": len(hits),
            "items": hits[offset : offset + limit],
        }

    @app.get("/cases/{case}/timeline")
    def timeline(case: str, limit: int = 100):
        require_case(case)
        docs = store.search(host=case, size=100000)
        rows = [
            {
                "timestamp": d.get("@timestamp") or "",
                "dataset": _dig(d, "event.dataset"),
                "category": _dig(d, "event.category"),
                "summary": _summary(d),
                "doc_id": d.get("_id"),
            }
            for d in docs
        ]
        rows.sort(key=lambda r: r["timestamp"], reverse=True)
        return rows[:limit]

    return app
