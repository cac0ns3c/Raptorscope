# SPDX-License-Identifier: GPL-3.0-or-later
from fastapi.testclient import TestClient

from raptorscope.api.app import create_app
from raptorscope.api.auth import AuthConfig
from tests.api.conftest import seed_docs
from raptorscope.api.store import InMemoryStore


def _client(**auth):
    store = InMemoryStore(seed_docs())
    return TestClient(create_app(store, auth=AuthConfig(**auth)))


def test_auth_disabled_by_default(client):
    # the default fixture app has no auth -> open
    assert client.get("/cases").status_code == 200
    assert client.get("/health").json()["auth"] is False


def test_protected_without_token_401():
    c = _client(username="analyst", password="s3cret")
    assert c.get("/health").status_code == 200  # health stays open
    assert c.get("/cases").status_code == 401
    assert c.get("/cases/mac-victim/alerts").status_code == 401


def test_login_returns_token_and_grants_access():
    c = _client(username="analyst", password="s3cret")
    bad = c.post("/login", json={"username": "analyst", "password": "wrong"})
    assert bad.status_code == 401

    ok = c.post("/login", json={"username": "analyst", "password": "s3cret"})
    assert ok.status_code == 200
    token = ok.json()["token"]

    headers = {"Authorization": f"Bearer {token}"}
    assert c.get("/cases", headers=headers).status_code == 200
    assert c.get("/cases/mac-victim/overview", headers=headers).status_code == 200


def test_bad_token_rejected():
    c = _client(username="analyst", password="s3cret")
    assert (
        c.get("/cases", headers={"Authorization": "Bearer nope"}).status_code == 401
    )


def test_token_expires():
    cfg = AuthConfig(username="analyst", password="s3cret", ttl_seconds=100)
    tok = cfg.token_for("analyst", "s3cret", now=1000)
    assert cfg.valid_token(tok, now=1050) is True
    assert cfg.valid_token(tok, now=1101) is False  # past TTL
    assert cfg.valid_token(tok, now=1000 - 5) is False  # issued in the future


def test_multi_user():
    cfg = AuthConfig(users={"alice": "pw1", "bob": "pw2"})
    assert cfg.enabled
    assert cfg.token_for("alice", "pw1") is not None
    assert cfg.token_for("bob", "pw2") is not None
    assert cfg.token_for("bob", "wrong") is None
    assert cfg.token_for("carol", "pw") is None
