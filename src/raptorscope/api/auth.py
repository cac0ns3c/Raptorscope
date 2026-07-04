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
import secrets
import time
from dataclasses import dataclass, field

from fastapi import Header, HTTPException

_DEFAULT_TTL = 8 * 3600  # 8 hours

# Role hierarchy: a higher rank implies every capability of the lower ones.
ROLE_RANK = {"viewer": 0, "analyst": 1, "admin": 2}
_DEFAULT_ROLE = "analyst"


@dataclass
class AuthConfig:
    users: dict = field(default_factory=dict)
    roles: dict = field(default_factory=dict)
    secret: str = "raptorscope"
    ttl_seconds: int = _DEFAULT_TTL

    def __init__(
        self,
        username: str = "",
        password: str = "",
        users: dict | None = None,
        roles: dict | None = None,
        secret: str = "raptorscope",
        ttl_seconds: int = _DEFAULT_TTL,
    ):
        self.users = dict(users or {})
        self.roles = dict(roles or {})
        if username and password:
            self.users[username] = password
        self.secret = secret
        self.ttl_seconds = ttl_seconds

    def role_of(self, username: str) -> str:
        """A configured role, or ``analyst`` by default (full case + AI access)."""
        return self.roles.get(username, _DEFAULT_ROLE)

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
        # Layout: issued.role.username — issued/role are dot-free, username is the
        # remainder (so usernames containing dots still decode unambiguously).
        payload = f"{issued}.{self.role_of(username)}.{username}"
        return f"{payload}.{self._sign(payload)}"

    def principal(
        self, token: str, now: float | None = None
    ) -> tuple[str, str] | None:
        """Return ``(username, role)`` for a valid, unexpired token, else None."""
        parts = token.rsplit(".", 1)
        if len(parts) != 2:
            return None
        payload, sig = parts
        if not hmac.compare_digest(sig, self._sign(payload)):
            return None
        try:
            issued_s, role, username = payload.split(".", 2)
            age = (now if now is not None else time.time()) - int(issued_s)
        except ValueError:
            return None
        if not (0 <= age <= self.ttl_seconds):
            return None
        return username, role

    def valid_token(self, token: str, now: float | None = None) -> bool:
        return self.principal(token, now) is not None

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
        # Optional per-user roles: RAPTORSCOPE_AUTH_ROLES="alice:admin,bob:viewer"
        roles: dict = {}
        for pair in os.environ.get("RAPTORSCOPE_AUTH_ROLES", "").split(","):
            if ":" in pair:
                name, role = pair.split(":", 1)
                if role.strip() in ROLE_RANK:
                    roles[name.strip()] = role.strip()
        # Never sign tokens with a guessable constant: use the configured secret,
        # else a strong per-process random one (tokens then reset on restart,
        # which is fine — they expire anyway).
        secret = os.environ.get("RAPTORSCOPE_AUTH_SECRET") or secrets.token_hex(32)
        return cls(
            users=users,
            roles=roles,
            secret=secret,
            ttl_seconds=int(os.environ.get("RAPTORSCOPE_AUTH_TTL", _DEFAULT_TTL)),
        )


def _bearer(authorization: str) -> str:
    prefix = "Bearer "
    return authorization[len(prefix):] if authorization.startswith(prefix) else ""


def make_auth_dependency(cfg: AuthConfig):
    def require_token(authorization: str = Header(default="")) -> None:
        if not cfg.enabled:
            return
        token = _bearer(authorization)
        if not token or not cfg.valid_token(token):
            raise HTTPException(status_code=401, detail="invalid or expired token")

    return require_token


def make_role_dependency(cfg: AuthConfig, min_role: str):
    """Dependency enforcing role >= ``min_role``. No-op when auth is disabled."""
    needed = ROLE_RANK[min_role]

    def require_role(authorization: str = Header(default="")) -> None:
        if not cfg.enabled:
            return
        prin = cfg.principal(_bearer(authorization))
        if prin is None:
            raise HTTPException(status_code=401, detail="invalid or expired token")
        _user, role = prin
        if ROLE_RANK.get(role, -1) < needed:
            raise HTTPException(
                status_code=403, detail=f"requires role '{min_role}' or higher"
            )

    return require_role
