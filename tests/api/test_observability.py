# SPDX-License-Identifier: GPL-3.0-or-later
"""Every response carries a correlation id; a caller-supplied one is echoed."""


def test_response_has_request_id(client):
    r = client.get("/health")
    assert r.headers.get("x-request-id")


def test_request_id_is_echoed(client):
    r = client.get("/health", headers={"x-request-id": "trace-123"})
    assert r.headers["x-request-id"] == "trace-123"


def test_metrics_endpoint_prometheus_format(client):
    client.get("/health")
    client.get("/cases")
    r = client.get("/metrics")
    assert r.status_code == 200
    assert "text/plain" in r.headers["content-type"]
    body = r.text
    assert "raptorscope_requests_total" in body
    assert "raptorscope_requests_by_status" in body
    assert "raptorscope_ai_requests_total" in body
