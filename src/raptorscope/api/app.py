# SPDX-License-Identifier: GPL-3.0-or-later
"""FastAPI application factory for the raptorscope query API.

``create_app(store)`` wires a :class:`~raptorscope.api.store.Store` into the
routes via closure, so tests build an app around a seeded ``InMemoryStore`` and
production builds one around ``ESStore``. A *case* is a collected host
(``host.name``).
"""
from fastapi import FastAPI, HTTPException

from .store import Store


def create_app(store: Store) -> FastAPI:
    app = FastAPI(title="Raptorscope API", version="0.1.0")

    def require_case(case: str) -> None:
        if case not in store.hosts():
            raise HTTPException(status_code=404, detail=f"unknown case: {case}")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app
