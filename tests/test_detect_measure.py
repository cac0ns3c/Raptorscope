# SPDX-License-Identifier: GPL-3.0-or-later
"""`raptorscope detect --measure` tallies per-rule fire counts (FP tuning)."""
import pathlib

from raptorscope.cli import measure_detections

ROOT = pathlib.Path(__file__).resolve().parents[1]
SAMPLE = str(ROOT / "samples" / "mac-victim")
RULES = str(ROOT / "detections" / "sigma")


def test_measure_reports_per_rule_counts():
    report = measure_detections(SAMPLE, RULES)
    assert report["docs"] > 0
    assert report["rules"] > 0
    assert report["alerts"] > 0
    # dirty sample fires several rules
    assert len(report["per_rule"]) > 0
    top = report["per_rule"][0]
    assert {"rule_id", "title", "level", "count"} <= top.keys()
    # sorted by count descending
    counts = [r["count"] for r in report["per_rule"]]
    assert counts == sorted(counts, reverse=True)
    assert sum(counts) == report["alerts"]
