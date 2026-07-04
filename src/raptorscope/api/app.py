# SPDX-License-Identifier: GPL-3.0-or-later
"""FastAPI application factory for the raptorscope query API.

``create_app(store)`` wires a :class:`~raptorscope.api.store.Store` into the
routes via closure, so tests build an app around a seeded ``InMemoryStore`` and
production builds one around ``ESStore``. A *case* is a collected host
(``host.name``).
"""
from collections import Counter

from fastapi import APIRouter, Depends, FastAPI, HTTPException
from pydantic import BaseModel

from ..detect.evaluate import load_rules, run_rules
from .auth import AuthConfig, make_auth_dependency
from .store import Store


class Credentials(BaseModel):
    username: str
    password: str

_LEVEL_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3, "informational": 4}


def _dig(doc: dict, path: str):
    cur = doc
    for key in path.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
    return cur


def _leaf_text(value) -> str:
    """Lowercased concatenation of every leaf value in a doc, for free-text search."""
    parts: list[str] = []

    def walk(v):
        if isinstance(v, dict):
            for x in v.values():
                walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)
        elif v is not None:
            parts.append(str(v))

    walk(value)
    return " ".join(parts).lower()


def _apply_op(cell, op: str, value: str) -> bool:
    if cell is None:
        return False
    s = str(cell)
    if op == "eq":
        return s == value
    if op == "startswith":
        return s.startswith(value)
    if op == "endswith":
        return s.endswith(value)
    return value.lower() in s.lower()  # default: contains


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


def create_app(
    store: Store,
    rules_dir: str = "detections/sigma",
    auth: AuthConfig | None = None,
) -> FastAPI:
    app = FastAPI(title="Raptorscope API", version="0.1.0")
    rules = load_rules(rules_dir)
    auth = auth or AuthConfig()
    require_token = make_auth_dependency(auth)
    # All /cases/* routes require a valid token when auth is enabled.
    router = APIRouter(dependencies=[Depends(require_token)])

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
        return {"status": "ok", "auth": auth.enabled}

    @app.post("/login")
    def login(creds: Credentials):
        token = auth.token_for(creds.username, creds.password)
        if token is None:
            raise HTTPException(status_code=401, detail="invalid credentials")
        return {"token": token}

    @router.get("/cases")
    def list_cases():
        return [case_summary(h) for h in store.hosts()]

    @router.get("/cases/{case}")
    def get_case(case: str):
        require_case(case)
        return case_summary(case)

    @router.get("/cases/{case}/overview")
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

    @router.get("/cases/{case}/artifacts/{dataset}")
    def artifact_view(case: str, dataset: str, limit: int = 50, offset: int = 0):
        require_case(case)
        hits = store.search(host=case, dataset=dataset, size=100000)
        return {
            "dataset": dataset,
            "total": len(hits),
            "items": hits[offset : offset + limit],
        }

    @router.get("/cases/{case}/timeline")
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

    @router.get("/cases/{case}/alerts")
    def alerts(case: str):
        require_case(case)
        docs = store.search(host=case, size=100000)
        fired = run_rules(docs, rules)
        fired.sort(
            key=lambda a: (_LEVEL_RANK.get(a["level"], 9), a["dataset"] or "")
        )
        return fired

    @router.get("/cases/{case}/search")
    def search(
        case: str,
        q: str = "",
        dataset: str | None = None,
        field: str | None = None,
        op: str = "contains",
        value: str | None = None,
        limit: int = 100,
    ):
        require_case(case)
        docs = store.search(host=case, dataset=dataset, size=100000)
        needle = q.strip().lower()
        hits = []
        for d in docs:
            if needle and needle not in _leaf_text(d):
                continue
            if field and value is not None and not _apply_op(
                _dig(d, field), op, value
            ):
                continue
            hits.append(d)
        return {"total": len(hits), "items": hits[:limit]}

    app.include_router(router)
    return app
