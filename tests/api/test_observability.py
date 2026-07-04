# SPDX-License-Identifier: GPL-3.0-or-later
"""Every response carries a correlation id; a caller-supplied one is echoed."""


def test_response_has_request_id(client):
    r = client.get("/health")
    assert r.headers.get("x-request-id")


def test_request_id_is_echoed(client):
    r = client.get("/health", headers={"x-request-id": "trace-123"})
    assert r.headers["x-request-id"] == "trace-123"
