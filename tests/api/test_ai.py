# SPDX-License-Identifier: GPL-3.0-or-later
"""AI features, exercised through a fake AIClient — no network, no API key."""
from fastapi.testclient import TestClient

from raptorscope.api.app import create_app
from raptorscope.api.store import InMemoryStore
from tests.api.conftest import seed_docs


class FakeAI:
    def text(self, system, user, max_tokens=1024):
        return "ANALYSIS: " + user[:60]

    def json(self, system, user, schema, max_tokens=1024):
        return {
            "q": "/private/tmp",
            "dataset": "macos.process",
            "field": "",
            "op": "contains",
            "value": "",
        }

    def agentic(self, system, user, tools, dispatch, max_tokens=2048, max_iters=6):
        # exercise the real dispatch so citations reflect actual case queries
        ov = dispatch("get_overview", {})
        hits = dispatch("search_case", {"q": "/private/tmp", "dataset": "macos.process"})
        assert "datasets" in ov and "items" in hits
        return {
            "answer": "VERDICT: the /private/tmp beacon is malicious.",
            "citations": [
                {"tool": "get_overview", "input": {}},
                {"tool": "search_case", "input": {"q": "/private/tmp"}},
            ],
        }


def _ai_client():
    return TestClient(create_app(InMemoryStore(seed_docs()), ai=FakeAI()))


def test_status_reflects_configuration():
    assert _ai_client().get("/ai/status").json()["enabled"] is True


def test_ai_disabled_returns_503(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    c = TestClient(create_app(InMemoryStore(seed_docs())))  # no ai, no key
    assert c.get("/ai/status").json()["enabled"] is False
    assert c.post("/cases/mac-victim/ai/summary").status_code == 503


def test_triage_analyzes_a_real_alert():
    c = _ai_client()
    alert = c.get("/cases/mac-victim/alerts").json()[0]
    r = c.post(
        "/cases/mac-victim/ai/triage",
        json={"rule_id": alert["rule_id"], "doc_id": alert["doc_id"]},
    )
    assert r.status_code == 200
    assert r.json()["analysis"].startswith("ANALYSIS:")


def test_triage_unknown_alert_404():
    c = _ai_client()
    r = c.post("/cases/mac-victim/ai/triage", json={"rule_id": "nope", "doc_id": "nope"})
    assert r.status_code == 404


def test_summary_returns_narrative():
    r = _ai_client().post("/cases/mac-victim/ai/summary")
    assert r.status_code == 200
    assert r.json()["summary"]


def test_nl_query_compiles_to_search_params():
    r = _ai_client().post(
        "/cases/mac-victim/ai/nl-query", json={"question": "processes from tmp"}
    )
    assert r.status_code == 200
    q = r.json()["query"]
    assert q["q"] == "/private/tmp"
    assert q["dataset"] == "macos.process"
    assert "field" not in q  # empty fields dropped


def test_copilot_returns_verdict_with_citations():
    r = _ai_client().post(
        "/cases/mac-victim/ai/copilot",
        json={"question": "Is this host compromised?"},
    )
    assert r.status_code == 200
    body = r.json()
    assert "VERDICT" in body["answer"]
    assert {c["tool"] for c in body["citations"]} == {"get_overview", "search_case"}


def test_ai_unknown_case_404():
    assert _ai_client().post(
        "/cases/nope/ai/summary"
    ).status_code == 404


def test_build_ai_is_configurable(monkeypatch):
    from raptorscope.ai.client import build_ai_from_env

    for k in ["ANTHROPIC_API_KEY", "RAPTORSCOPE_AI_KEY", "ANTHROPIC_BASE_URL"]:
        monkeypatch.delenv(k, raising=False)
    assert build_ai_from_env() is None  # no key -> disabled

    monkeypatch.setenv("RAPTORSCOPE_AI_KEY", "sk-test")
    monkeypatch.setenv("RAPTORSCOPE_AI_MODEL", "claude-test-model")
    monkeypatch.setenv("RAPTORSCOPE_AI_BASE_URL", "https://gateway.example/v1")
    ai = build_ai_from_env()
    assert ai is not None
    assert ai.model == "claude-test-model"
    assert "gateway.example" in str(ai._client.base_url)
