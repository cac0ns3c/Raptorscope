# SPDX-License-Identifier: GPL-3.0-or-later


def test_alerts_fire_across_every_dataset(client):
    r = client.get("/cases/mac-victim/alerts")
    assert r.status_code == 200
    alerts = r.json()
    assert alerts
    # every v1 dataset has at least one firing detection in the dirty case
    assert {a["dataset"] for a in alerts} == {
        "macos.persistence",
        "macos.process",
        "macos.quarantine",
        "macos.tcc",
        "macos.inventory",
    }
    for a in alerts:
        assert a["rule_id"] and a["title"] and a["doc_id"]
        assert a["evidence"]


def test_alerts_sorted_by_severity(client):
    alerts = client.get("/cases/mac-victim/alerts").json()
    rank = {"high": 0, "medium": 1, "low": 2, "informational": 3}
    levels = [rank.get(a["level"], 9) for a in alerts]
    assert levels == sorted(levels)


def test_alert_doc_id_pivots_to_evidence(client):
    alerts = client.get("/cases/mac-victim/alerts").json()
    a = next(x for x in alerts if x["dataset"] == "macos.quarantine")
    items = client.get(
        f"/cases/mac-victim/artifacts/{a['dataset']}?limit=1000"
    ).json()["items"]
    assert a["doc_id"] in {d["_id"] for d in items}


def test_clean_case_has_no_alerts(client):
    assert client.get("/cases/mac-clean/alerts").json() == []


def test_alerts_unknown_case_404(client):
    assert client.get("/cases/nope/alerts").status_code == 404
