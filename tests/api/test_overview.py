# SPDX-License-Identifier: GPL-3.0-or-later
from tests.api.conftest import DIRTY_DOC_COUNT


def test_overview_aggregations(client):
    r = client.get("/cases/mac-victim/overview")
    assert r.status_code == 200
    ov = r.json()
    assert ov["total"] == DIRTY_DOC_COUNT
    assert ov["datasets"]["macos.persistence"] == 12
    assert ov["datasets"]["macos.process"] == 3
    # persistence family fully represented
    types = ov["persistence_types"]
    assert types["launch_agent"] == 2
    assert types["launch_daemon"] == 2
    assert types["login_item"] == 2
    assert types["cron"] == 2
    assert types["config_profile"] == 2
    assert types["btm"] == 2
    # one unsigned process (the /private/tmp beacon) and one unsigned app
    assert ov["unsigned"]["process"] == 1
    assert ov["unsigned"]["inventory"] == 1


def test_overview_unknown_case_404(client):
    assert client.get("/cases/nope/overview").status_code == 404
