# SPDX-License-Identifier: GPL-3.0-or-later
"""Role-based access control + audit logging (D1)."""
import logging

from fastapi.testclient import TestClient

from raptorscope.api.app import create_app
from raptorscope.api.auth import AuthConfig
from raptorscope.api.store import InMemoryStore
from tests.api.conftest import seed_docs
from tests.api.test_ai import FakeAI


def _app(roles=None, users=None):
    auth = AuthConfig(users=users or {"v": "pw", "a": "pw"},
                      roles=roles, secret="s")
    return TestClient(create_app(InMemoryStore(seed_docs()), auth=auth, ai=FakeAI()))


def _login(c, u, p):
    return c.post("/login", json={"username": u, "password": p}).json()["token"]


def _h(t):
    return {"Authorization": f"Bearer {t}"}


def test_token_embeds_role_and_decodes():
    cfg = AuthConfig(users={"a": "pw"}, roles={"a": "admin"}, secret="s")
    tok = cfg.token_for("a", "pw")
    assert cfg.principal(tok) == ("a", "admin")
    assert cfg.valid_token(tok)


def test_dotted_username_round_trips():
    cfg = AuthConfig(users={"a.b@x": "pw"}, roles={"a.b@x": "viewer"}, secret="s")
    tok = cfg.token_for("a.b@x", "pw")
    assert cfg.principal(tok) == ("a.b@x", "viewer")


def test_viewer_is_read_only_analyst_can_act():
    c = _app(roles={"v": "viewer", "a": "analyst"})
    vt, at = _login(c, "v", "pw"), _login(c, "a", "pw")
    # viewer reads case data fine
    assert c.get("/cases", headers=_h(vt)).status_code == 200
    assert c.get("/cases/mac-victim/overview", headers=_h(vt)).status_code == 200
    # ...but is blocked from AI + fleet hunt
    assert c.post("/cases/mac-victim/ai/summary", headers=_h(vt)).status_code == 403
    assert c.get("/hunt?q=x", headers=_h(vt)).status_code == 403
    # analyst can
    assert c.post("/cases/mac-victim/ai/summary", headers=_h(at)).status_code == 200
    assert c.get("/hunt?q=x", headers=_h(at)).status_code == 200


def test_default_role_is_analyst():
    c = _app(users={"u": "pw"})  # no explicit roles
    t = _login(c, "u", "pw")
    assert c.post("/cases/mac-victim/ai/summary", headers=_h(t)).status_code == 200


def test_audit_logs_case_and_ai_access(caplog):
    c = TestClient(create_app(InMemoryStore(seed_docs())))  # auth off
    with caplog.at_level(logging.INFO, logger="raptorscope.audit"):
        c.get("/cases/mac-victim/overview")
    msgs = [r.getMessage() for r in caplog.records if r.name == "raptorscope.audit"]
    assert any("/cases/mac-victim/overview" in m and "user=" in m for m in msgs)
