# SPDX-License-Identifier: GPL-3.0-or-later
"""Optional bearer-token auth for the query API.

Auth is **off by default** (the offline demo stays zero-setup). Configure a
username + password (via ``raptorscope serve --auth-user/--auth-pass`` or the
``RAPTORSCOPE_AUTH_USER``/``RAPTORSCOPE_AUTH_PASS`` env vars) to require a token:
clients call ``POST /login`` with the credentials, receive a token, and send it
as ``Authorization: Bearer <token>`` on every ``/cases/*`` request.
"""
import hashlib
import hmac
import os
from dataclasses import dataclass

from fastapi import Header, HTTPException


@dataclass
class AuthConfig:
    username: str = ""
    password: str = ""
    secret: str = "raptorscope"

    @property
    def enabled(self) -> bool:
        return bool(self.password)

    def token_for(self, username: str, password: str) -> str | None:
        """Return a bearer token if the credentials are valid, else ``None``."""
        if not self.enabled:
            return None
        if hmac.compare_digest(username, self.username) and hmac.compare_digest(
            password, self.password
        ):
            return self._token()
        return None

    def _token(self) -> str:
        # Deterministic token bound to the configured credentials + secret.
        msg = f"{self.username}:{self.password}".encode()
        return hmac.new(self.secret.encode(), msg, hashlib.sha256).hexdigest()

    def valid_token(self, token: str) -> bool:
        return hmac.compare_digest(token, self._token())

    @classmethod
    def from_env(cls) -> "AuthConfig":
        return cls(
            username=os.environ.get("RAPTORSCOPE_AUTH_USER", ""),
            password=os.environ.get("RAPTORSCOPE_AUTH_PASS", ""),
            secret=os.environ.get("RAPTORSCOPE_AUTH_SECRET", "raptorscope"),
        )


def make_auth_dependency(cfg: AuthConfig):
    def require_token(authorization: str = Header(default="")) -> None:
        if not cfg.enabled:
            return
        prefix = "Bearer "
        token = authorization[len(prefix):] if authorization.startswith(prefix) else ""
        if not token or not cfg.valid_token(token):
            raise HTTPException(status_code=401, detail="invalid or missing token")

    return require_token
