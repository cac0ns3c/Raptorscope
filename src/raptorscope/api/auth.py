# SPDX-License-Identifier: GPL-3.0-or-later
"""Optional bearer-token auth for the query API.

Auth is **off by default** (the offline demo stays zero-setup). Configure one or
more username/password pairs to require a token: clients ``POST /login`` and
receive a **time-limited** bearer token they send as ``Authorization: Bearer
<token>`` on every ``/cases/*`` request. Tokens are stateless and signed — the
server keeps no session — and expire after ``ttl_seconds``.

Configure via ``raptorscope serve --auth-user/--auth-pass`` or env:
``RAPTORSCOPE_AUTH_USER``/``RAPTORSCOPE_AUTH_PASS`` (single user) or
``RAPTORSCOPE_AUTH_USERS="alice:pw1,bob:pw2"`` (multiple).
"""
import hashlib
import hmac
import os
import time
from dataclasses import dataclass, field

from fastapi import Header, HTTPException

_DEFAULT_TTL = 8 * 3600  # 8 hours


@dataclass
class AuthConfig:
    users: dict = field(default_factory=dict)
    secret: str = "raptorscope"
    ttl_seconds: int = _DEFAULT_TTL

    def __init__(
        self,
        username: str = "",
        password: str = "",
        users: dict | None = None,
        secret: str = "raptorscope",
        ttl_seconds: int = _DEFAULT_TTL,
    ):
        self.users = dict(users or {})
        if username and password:
            self.users[username] = password
        self.secret = secret
        self.ttl_seconds = ttl_seconds

    @property
    def enabled(self) -> bool:
        return bool(self.users)

    def _sign(self, payload: str) -> str:
        return hmac.new(
            self.secret.encode(), payload.encode(), hashlib.sha256
        ).hexdigest()

    def token_for(
        self, username: str, password: str, now: float | None = None
    ) -> str | None:
        """Return a signed, time-stamped token if credentials are valid."""
        if not self.enabled:
            return None
        expected = self.users.get(username)
        if expected is None or not hmac.compare_digest(password, expected):
            return None
        issued = int(now if now is not None else time.time())
        payload = f"{username}.{issued}"
        return f"{payload}.{self._sign(payload)}"

    def valid_token(self, token: str, now: float | None = None) -> bool:
        parts = token.rsplit(".", 1)
        if len(parts) != 2:
            return False
        payload, sig = parts
        if not hmac.compare_digest(sig, self._sign(payload)):
            return False
        try:
            _username, issued = payload.rsplit(".", 1)
            age = (now if now is not None else time.time()) - int(issued)
        except ValueError:
            return False
        return 0 <= age <= self.ttl_seconds

    @classmethod
    def from_env(cls) -> "AuthConfig":
        users: dict = {}
        multi = os.environ.get("RAPTORSCOPE_AUTH_USERS", "")
        for pair in multi.split(","):
            if ":" in pair:
                u, p = pair.split(":", 1)
                users[u.strip()] = p.strip()
        u = os.environ.get("RAPTORSCOPE_AUTH_USER", "")
        p = os.environ.get("RAPTORSCOPE_AUTH_PASS", "")
        if u and p:
            users[u] = p
        return cls(
            users=users,
            secret=os.environ.get("RAPTORSCOPE_AUTH_SECRET", "raptorscope"),
            ttl_seconds=int(os.environ.get("RAPTORSCOPE_AUTH_TTL", _DEFAULT_TTL)),
        )


def make_auth_dependency(cfg: AuthConfig):
    def require_token(authorization: str = Header(default="")) -> None:
        if not cfg.enabled:
            return
        prefix = "Bearer "
        token = authorization[len(prefix):] if authorization.startswith(prefix) else ""
        if not token or not cfg.valid_token(token):
            raise HTTPException(status_code=401, detail="invalid or expired token")

    return require_token
