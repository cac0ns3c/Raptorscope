# SPDX-License-Identifier: GPL-3.0-or-later
"""FastAPI application factory for the raptorscope query API.

``create_app(store)`` wires a :class:`~raptorscope.api.store.Store` into the
routes via closure, so tests build an app around a seeded ``InMemoryStore`` and
production builds one around ``ESStore``. A *case* is a collected host
(``host.name``).
"""
import logging
import os
import time
import uuid

import json as _json

from fastapi import APIRouter, Depends, FastAPI, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse, StreamingResponse
from pydantic import BaseModel

_log = logging.getLogger("raptorscope.ai")
_access = logging.getLogger("raptorscope.access")
_audit = logging.getLogger("raptorscope.audit")


class _Metrics:
    """Minimal in-process counters exposed in Prometheus text format."""

    def __init__(self):
        self.requests = 0
        self.by_status: dict[str, int] = {}
        self.ai_requests = 0

    def observe(self, path: str, status: int) -> None:
        self.requests += 1
        cls = f"{status // 100}xx"
        self.by_status[cls] = self.by_status.get(cls, 0) + 1
        if "/ai/" in path and not path.endswith("/ai/status"):
            self.ai_requests += 1

    def render(self) -> str:
        lines = [
            "# HELP raptorscope_requests_total Total HTTP requests",
            "# TYPE raptorscope_requests_total counter",
            f"raptorscope_requests_total {self.requests}",
            "# HELP raptorscope_requests_by_status HTTP requests by status class",
            "# TYPE raptorscope_requests_by_status counter",
        ]
        for cls, n in sorted(self.by_status.items()):
            lines.append(f'raptorscope_requests_by_status{{class="{cls}"}} {n}')
        lines += [
            "# HELP raptorscope_ai_requests_total AI endpoint requests",
            "# TYPE raptorscope_ai_requests_total counter",
            f"raptorscope_ai_requests_total {self.ai_requests}",
        ]
        return "\n".join(lines) + "\n"


class _RateLimiter:
    """Fixed-window per-client request counter (in-memory, per app instance)."""

    def __init__(self, limit: int, window: float = 60.0):
        self.limit = limit
        self.window = window
        self._hits: dict[str, tuple[float, int]] = {}

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        start, count = self._hits.get(key, (now, 0))
        if now - start >= self.window:
            start, count = now, 0
        count += 1
        self._hits[key] = (start, count)
        return count <= self.limit

from ..ai import service as ai_service
from ..ai.client import AIClient, MODEL, build_ai_from_env
from ..detect.evaluate import load_rules, run_rules
from .auth import (
    AuthConfig,
    _bearer,
    make_auth_dependency,
    make_role_dependency,
)
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
    ai_rate: int | None = None,
    login_rate: int | None = None,
    detector=None,
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

    # Per-client rate limits (fixed 60s window) for abuse/cost protection.
    ai_limit = ai_rate if ai_rate is not None else int(os.environ.get("RAPTORSCOPE_AI_RATE", "60"))
    login_limit = (
        login_rate if login_rate is not None else int(os.environ.get("RAPTORSCOPE_LOGIN_RATE", "20"))
    )
    ai_bucket = _RateLimiter(ai_limit)
    login_bucket = _RateLimiter(login_limit)
    metrics = _Metrics()

    @app.get("/metrics")
    def prometheus_metrics():
        return PlainTextResponse(metrics.render())

    # Registered FIRST so it is the INNERMOST middleware — a 429 it returns still
    # passes back out through _access_log below (which is registered last and so
    # wraps it), keeping throttled abuse in the access log, metrics, and audit trail.
    @app.middleware("http")
    async def _rate_limit(request, call_next):
        path = request.url.path
        key = request.client.host if request.client else "?"
        bucket = None
        if path == "/login":
            bucket = login_bucket
        elif "/ai/" in path and not path.endswith("/ai/status"):
            bucket = ai_bucket
        if bucket is not None and not bucket.allow(key):
            return JSONResponse(
                status_code=429, content={"detail": "rate limit exceeded"}
            )
        return await call_next(request)

    # Registered LAST -> outermost: observes/audits EVERY response, including the
    # 429s produced by _rate_limit above.
    @app.middleware("http")
    async def _access_log(request, call_next):
        rid = request.headers.get("x-request-id") or uuid.uuid4().hex[:12]
        start = time.monotonic()
        response = await call_next(request)
        response.headers["X-Request-ID"] = rid
        path = request.url.path
        metrics.observe(path, response.status_code)
        _access.info(
            "rid=%s %s %s -> %s %.1fms",
            rid,
            request.method,
            path,
            response.status_code,
            (time.monotonic() - start) * 1000,
        )
        # Audit trail: who touched case data / AI / hunt, and the outcome.
        if path.startswith("/cases") or path.startswith("/hunt") or "/ai/" in path:
            user = "-"
            if auth.enabled:
                prin = auth.principal(_bearer(request.headers.get("authorization", "")))
                user = prin[0] if prin else "anon"
            _audit.info(
                "rid=%s user=%s %s %s -> %s",
                rid, user, request.method, path, response.status_code,
            )
        return response
    require_token = make_auth_dependency(auth)
    # Active/costly actions (AI, fleet hunt) require analyst+; viewers are read-only.
    require_analyst = Depends(make_role_dependency(auth, "analyst"))
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
        return {"case": case, "total": store.count(host=case), **store.aggregate(host=case)}

    @router.get("/cases/{case}/artifacts/{dataset}")
    def artifact_view(case: str, dataset: str, limit: int = 50, offset: int = 0):
        require_case(case)
        # Page ES-side (from+size) instead of pulling the whole dataset into memory.
        return {
            "dataset": dataset,
            "total": store.count(host=case, dataset=dataset),
            "items": store.search(
                host=case, dataset=dataset, size=limit, offset=offset
            ),
        }

    @router.get("/cases/{case}/artifacts/{dataset}/page")
    def artifact_page(case: str, dataset: str, limit: int = 50, cursor: str = ""):
        """Deep cursor pagination (PIT + search_after on ES) past the 10k window."""
        require_case(case)
        res = store.page(
            host=case, dataset=dataset, size=limit, cursor=cursor or None
        )
        return {"dataset": dataset, "items": res["items"], "cursor": res["cursor"]}

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
                "time_source": _dig(d, "raptorscope.time.source"),
            }
            for d in docs
        ]
        rows.sort(key=lambda r: r["timestamp"], reverse=True)
        return rows[:limit]

    def _fired(case: str) -> list[dict]:
        """Fired alerts for a case. Uses the ES-native detector when configured
        (no full-doc pull); falls back to the in-process evaluator otherwise."""
        if detector is not None:
            return detector.run(host=case)
        return run_rules(store.search(host=case, size=100000), rules)

    @router.get("/cases/{case}/alerts")
    def alerts(case: str):
        require_case(case)
        fired = _fired(case)
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
        return {"case": case, "total": store.count(host=case), **store.aggregate(host=case)}

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

    @router.post("/cases/{case}/ai/triage", dependencies=[require_analyst])
    def ai_triage(case: str, body: TriageBody):
        require_case(case)
        _require_ai()
        fired = _fired(case)
        alert = next(
            (a for a in fired if a["rule_id"] == body.rule_id and a["doc_id"] == body.doc_id),
            None,
        )
        if alert is None:
            raise HTTPException(status_code=404, detail="alert not found")
        return _ai_call(
            lambda: ai_service.triage_alert(ai, alert, store.get(body.doc_id) or {})
        )

    def _summary_inputs(case: str):
        docs = store.search(host=case, size=100000)
        fired = _fired(case)
        fired.sort(key=lambda a: (_LEVEL_RANK.get(a["level"], 9), a["dataset"] or ""))
        # Chronological (ascending) event timeline so the model can tell the story.
        events = sorted(
            (
                {
                    "timestamp": d.get("@timestamp") or "",
                    "dataset": _dig(d, "event.dataset"),
                    "summary": _summary(d),
                    "time_source": _dig(d, "raptorscope.time.source"),
                }
                for d in docs
            ),
            key=lambda e: e["timestamp"],
        )
        return _overview(case), fired, events

    @router.post("/cases/{case}/ai/summary", dependencies=[require_analyst])
    def ai_summary(case: str):
        require_case(case)
        _require_ai()
        ov, fired, events = _summary_inputs(case)
        return _ai_call(lambda: ai_service.summarize_case(ai, ov, fired, events))

    @router.post("/cases/{case}/ai/summary/stream", dependencies=[require_analyst])
    def ai_summary_stream(case: str):
        require_case(case)
        _require_ai()
        ov, fired, events = _summary_inputs(case)

        def gen():
            try:
                for chunk in ai_service.stream_summary(ai, ov, fired, events):
                    yield f"data: {_json.dumps({'text': chunk})}\n\n"
                yield 'data: {"done": true}\n\n'
            except Exception as e:  # noqa: BLE001 - surface as a stream error event
                _log.warning("AI stream error: %s", e)
                yield 'data: {"error": true}\n\n'

        return StreamingResponse(gen(), media_type="text/event-stream")

    @router.post("/cases/{case}/ai/nl-query", dependencies=[require_analyst])
    def ai_nl_query(case: str, body: QuestionBody):
        require_case(case)
        _require_ai()
        return _ai_call(
            lambda: ai_service.compile_query(ai, body.question, store.datasets(host=case))
        )

    @router.post("/cases/{case}/ai/iocs", dependencies=[require_analyst])
    def ai_iocs(case: str):
        require_case(case)
        _require_ai()
        return _ai_call(lambda: ai_service.extract_iocs(ai, _fired(case)))

    def _copilot_dispatch(case: str):
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
                return _fired(case)[:50]
            if name == "get_overview":
                return _overview(case)
            return {"error": f"unknown tool {name}"}

        return dispatch

    @router.post("/cases/{case}/ai/copilot", dependencies=[require_analyst])
    def ai_copilot(case: str, body: QuestionBody):
        require_case(case)
        _require_ai()
        return _ai_call(
            lambda: ai_service.run_copilot(ai, body.question, _copilot_dispatch(case))
        )

    @router.post("/cases/{case}/ai/copilot/stream", dependencies=[require_analyst])
    def ai_copilot_stream(case: str, body: QuestionBody):
        require_case(case)
        _require_ai()
        dispatch = _copilot_dispatch(case)

        def gen():
            try:
                for ev in ai_service.stream_copilot(ai, body.question, dispatch):
                    yield f"data: {_json.dumps(ev)}\n\n"
                yield 'data: {"done": true}\n\n'
            except Exception as e:  # noqa: BLE001 - surface as a stream error event
                _log.warning("AI copilot stream error: %s", e)
                yield 'data: {"error": true}\n\n'

        return StreamingResponse(gen(), media_type="text/event-stream")

    @router.get("/hunt", dependencies=[require_analyst])
    def hunt(q: str, limit: int = 200):
        """Cross-host IOC hunt: where does an indicator appear across the fleet?"""
        docs = store.hunt(q.strip(), size=limit) if q.strip() else []
        by_host: dict[str, dict] = {}
        for d in docs:
            h = _dig(d, "host.name") or "?"
            entry = by_host.setdefault(
                h, {"host": h, "count": 0, "datasets": set(), "samples": []}
            )
            entry["count"] += 1
            ds = _dig(d, "event.dataset")
            if ds:
                entry["datasets"].add(ds)
            if len(entry["samples"]) < 5:
                entry["samples"].append(
                    {"dataset": ds, "summary": _summary(d), "doc_id": d.get("_id")}
                )
        hosts = sorted(by_host.values(), key=lambda e: e["count"], reverse=True)
        for e in hosts:
            e["datasets"] = sorted(e["datasets"])
        return {
            "value": q,
            "total": len(docs),
            "host_count": len(hosts),
            "hosts": hosts,
        }

    app.include_router(router)
    return app
