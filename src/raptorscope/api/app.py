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

    return app
