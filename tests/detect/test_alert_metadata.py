# SPDX-License-Identifier: GPL-3.0-or-later
"""Alerts carry the rule's detection metadata (MITRE, description, FP, status)."""
import json
import pathlib

from raptorscope.detect.evaluate import load_rules, mitre_techniques, run_rules
from raptorscope.normalize.tcc import normalize_tcc

RULES = load_rules("detections/sigma")
HOST = {"name": "h", "os": {"type": "macos"}}


def test_mitre_parser():
    assert mitre_techniques(["attack.persistence", "attack.t1547.015"]) == ["T1547.015"]
    assert mitre_techniques(["attack.t1056.001", "attack.t1113"]) == ["T1056.001", "T1113"]


def test_alert_carries_detection_metadata():
    rows = json.loads(pathlib.Path("fixtures/velociraptor/tcc.raw.json").read_text())
    alerts = run_rules(normalize_tcc(rows, HOST), RULES)
    assert alerts, "expected the tcc fixture to fire at least one rule"
    a = alerts[0]
    for key in ("mitre", "description", "falsepositives", "status"):
        assert key in a, f"alert missing {key}"
    assert isinstance(a["mitre"], list)
    assert a["status"]  # non-empty
    # at least one fired alert has a MITRE technique + a description
    assert any(x["mitre"] for x in alerts)
    assert any(x["description"] for x in alerts)
