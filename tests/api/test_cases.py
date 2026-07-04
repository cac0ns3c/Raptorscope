# SPDX-License-Identifier: GPL-3.0-or-later
from tests.api.conftest import CLEAN_DOC_COUNT, DIRTY_DOC_COUNT


def test_list_cases(client):
    r = client.get("/cases")
    assert r.status_code == 200
    cases = {c["name"]: c for c in r.json()}
    assert set(cases) == {"mac-victim", "mac-clean"}
    assert cases["mac-victim"]["doc_count"] == DIRTY_DOC_COUNT
    assert cases["mac-clean"]["doc_count"] == CLEAN_DOC_COUNT
    assert "macos.persistence" in cases["mac-victim"]["datasets"]


def test_get_one_case(client):
    r = client.get("/cases/mac-victim")
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "mac-victim"
    assert body["doc_count"] == DIRTY_DOC_COUNT
    assert "macos.tcc" in body["datasets"]


def test_unknown_case_404(client):
    r = client.get("/cases/nope")
    assert r.status_code == 404
