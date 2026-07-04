# SPDX-License-Identifier: GPL-3.0-or-later
import json
import pathlib

from raptorscope.detect.evaluate import load_rules, rule_matches, run_rules
from raptorscope.normalize.inventory import normalize_inventory
from raptorscope.normalize.launch_items import normalize_launch_items
from raptorscope.normalize.processes import normalize_processes
from raptorscope.normalize.tcc import normalize_tcc

FIX = pathlib.Path("fixtures/velociraptor")
HOST = {"name": "h", "os": {"type": "macos"}}
RULES = load_rules("detections/sigma")


def _rows(name):
    return json.loads((FIX / name).read_text())


def test_load_rules_have_metadata():
    assert RULES
    for r in RULES:
        assert r.id and r.title and r.level
        assert r.datasets  # every rule targets at least one dataset


def test_condition_boolean_and_not():
    detection = {
        "selection": {"event.dataset": "macos.tcc", "raptorscope.tcc.allowed": True},
        "filter": {"raptorscope.tcc.client|startswith": "com.apple."},
        "condition": "selection and not filter",
    }
    apple = {"event": {"dataset": "macos.tcc"}, "raptorscope": {"tcc": {"allowed": True, "client": "com.apple.Terminal"}}}
    other = {"event": {"dataset": "macos.tcc"}, "raptorscope": {"tcc": {"allowed": True, "client": "us.zoom.xos"}}}
    assert rule_matches(apple, detection) is False
    assert rule_matches(other, detection) is True


def test_persistence_rule_fires_only_on_suspicious_rows():
    docs = normalize_launch_items(_rows("launch_items.raw.json"), HOST)
    alerts = run_rules(docs, RULES)
    fired_paths = {a["evidence"].get("file.path") for a in alerts}
    assert "/Users/Shared/.cache/com.system.helper.plist" in fired_paths
    # benign Apple/Google launch items never fire
    assert "/Library/LaunchDaemons/com.apple.softwareupdated.plist" not in fired_paths


def test_tcc_exclusion_of_apple_clients():
    docs = normalize_tcc(_rows("tcc.raw.json"), HOST)
    alerts = [a for a in run_rules(docs, RULES) if a["dataset"] == "macos.tcc"]
    clients = {a["evidence"].get("raptorscope.tcc.client") for a in alerts}
    assert "/Users/Shared/.helper/agent" in clients  # non-apple accessibility grant
    assert "com.apple.Terminal" not in clients  # apple excluded
    assert "us.zoom.xos" not in clients  # camera is not a sensitive service


def test_inventory_unsigned_outside_applications():
    docs = normalize_inventory(_rows("installed_apps.raw.json"), HOST)
    alerts = [a for a in run_rules(docs, RULES) if a["dataset"] == "macos.inventory"]
    paths = {a["evidence"].get("file.path") for a in alerts}
    # only the unsigned app outside /Applications fires; Slack does not
    assert paths == {"/Users/analyst/.local/Updater.app"}


def test_alert_shape_and_doc_id():
    docs = normalize_processes(_rows("processes.raw.json"), HOST)
    for i, d in enumerate(docs):
        d["_id"] = str(i)
    alerts = run_rules(docs, RULES)
    assert alerts
    a = alerts[0]
    assert {"rule_id", "title", "level", "dataset", "doc_id", "evidence"} <= set(a)
    assert a["doc_id"] is not None
