# SPDX-License-Identifier: GPL-3.0-or-later
"""FastAPI application factory for the raptorscope query API.

``create_app(store)`` wires a :class:`~raptorscope.api.store.Store` into the
routes via closure, so tests build an app around a seeded ``InMemoryStore`` and
production builds one around ``ESStore``. A *case* is a collected host
(``host.name``).
"""
import logging
from collections import Counter

from fastapi import APIRouter, Depends, FastAPI, HTTPException
from pydantic import BaseModel

_log = logging.getLogger("raptorscope.ai")

from ..ai import service as ai_service
from ..ai.client import AIClient, MODEL, build_ai_from_env
from ..detect.evaluate import load_rules, run_rules
from .auth import AuthConfig, make_auth_dependency
from .docs import get_doc, list_docs
from .store import Store


class Credentials(BaseModel):
    username: str
    password: str


class TriageBody(BaseModel):
    rule_id: str
    doc_id: str


class QuestionBody(BaseModel):
    question: str

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
    ai: AIClient | None = None,
) -> FastAPI:
    # Disable the built-in Swagger/ReDoc UIs so `/docs` serves our own guides.
    app = FastAPI(
        title="Raptorscope API",
        version="0.1.0",
        docs_url=None,
        redoc_url=None,
    )
    rules = load_rules(rules_dir)
    ai = ai if ai is not None else build_ai_from_env()
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

    # Docs are public (no case data) so they're readable even before login.
    @app.get("/docs")
    def docs_index():
        return list_docs()

    @app.get("/docs/{doc_id}")
    def doc(doc_id: str):
        d = get_doc(doc_id)
        if d is None:
            raise HTTPException(status_code=404, detail="unknown doc")
        return d

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

    # ---- AI features (opt-in; require ANTHROPIC_API_KEY or an injected client) ----
    def _overview(case: str) -> dict:
        docs = store.search(host=case, size=100000)
        return {
            "case": case,
            "total": len(docs),
            "datasets": dict(Counter(_dig(d, "event.dataset") for d in docs)),
            "persistence_types": dict(
                Counter(
                    _dig(d, "raptorscope.persistence.type")
                    for d in docs
                    if _dig(d, "event.dataset") == "macos.persistence"
                )
            ),
            "unsigned": {
                "process": sum(
                    1
                    for d in docs
                    if _dig(d, "event.dataset") == "macos.process"
                    and _dig(d, "process.code_signature.trusted") is not True
                ),
                "inventory": sum(
                    1
                    for d in docs
                    if _dig(d, "event.dataset") == "macos.inventory"
                    and _dig(d, "raptorscope.app.signed") is False
                ),
            },
        }

    def _search(case, q="", dataset=None, field=None, op="contains", value=None, limit=20):
        docs = store.search(host=case, dataset=dataset, size=100000)
        needle = (q or "").strip().lower()
        hits = []
        for d in docs:
            if needle and needle not in _leaf_text(d):
                continue
            if field and value is not None and not _apply_op(_dig(d, field), op, value):
                continue
            hits.append(d)
        return {"total": len(hits), "items": hits[:limit]}

    def _require_ai():
        if ai is None:
            raise HTTPException(
                status_code=503,
                detail="AI features are not configured (set ANTHROPIC_API_KEY).",
            )

    def _ai_call(fn):
        """Run an AI service call, mapping upstream LLM errors to a clean 502.

        The provider's raw message is logged server-side but never returned to the
        client — only the exception class name — so request bodies, tokens, or
        other sensitive detail can't leak through the error response.
        """
        try:
            return fn()
        except HTTPException:
            raise
        except Exception as e:  # noqa: BLE001 - surface provider errors cleanly
            _log.warning("AI provider error: %s", e)
            raise HTTPException(
                status_code=502,
                detail=f"AI provider request failed ({type(e).__name__}).",
            )

    @app.get("/ai/status")
    def ai_status():
        return {
            "enabled": ai is not None,
            "model": getattr(ai, "model", MODEL) if ai is not None else None,
        }

    @router.post("/cases/{case}/ai/triage")
    def ai_triage(case: str, body: TriageBody):
        require_case(case)
        _require_ai()
        docs = store.search(host=case, size=100000)
        fired = run_rules(docs, rules)
        alert = next(
            (a for a in fired if a["rule_id"] == body.rule_id and a["doc_id"] == body.doc_id),
            None,
        )
        if alert is None:
            raise HTTPException(status_code=404, detail="alert not found")
        return _ai_call(
            lambda: ai_service.triage_alert(ai, alert, store.get(body.doc_id) or {})
        )

    @router.post("/cases/{case}/ai/summary")
    def ai_summary(case: str):
        require_case(case)
        _require_ai()
        docs = store.search(host=case, size=100000)
        fired = run_rules(docs, rules)
        fired.sort(key=lambda a: (_LEVEL_RANK.get(a["level"], 9), a["dataset"] or ""))
        return _ai_call(lambda: ai_service.summarize_case(ai, _overview(case), fired))

    @router.post("/cases/{case}/ai/nl-query")
    def ai_nl_query(case: str, body: QuestionBody):
        require_case(case)
        _require_ai()
        return _ai_call(
            lambda: ai_service.compile_query(ai, body.question, store.datasets(host=case))
        )

    @router.post("/cases/{case}/ai/copilot")
    def ai_copilot(case: str, body: QuestionBody):
        require_case(case)
        _require_ai()

        def dispatch(name: str, inp: dict):
            if name == "search_case":
                return _search(
                    case,
                    q=inp.get("q", ""),
                    dataset=inp.get("dataset") or None,
                    field=inp.get("field") or None,
                    op=inp.get("op", "contains"),
                    value=inp.get("value"),
                    limit=int(inp.get("limit", 20)),
                )
            if name == "list_alerts":
                return run_rules(store.search(host=case, size=100000), rules)[:50]
            if name == "get_overview":
                return _overview(case)
            return {"error": f"unknown tool {name}"}

        return _ai_call(lambda: ai_service.run_copilot(ai, body.question, dispatch))

    app.include_router(router)
    return app
