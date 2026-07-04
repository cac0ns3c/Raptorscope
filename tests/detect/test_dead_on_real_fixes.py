# SPDX-License-Identifier: GPL-3.0-or-later
"""Fixes for the two rules the multi-agent review found dead on REAL captures:
quarantine keyed on a filename real QuarantineEventsV2 lacks, and process keyed on
signature data stock Pslist lacks."""
from raptorscope.detect.evaluate import load_rules, run_rules
from raptorscope.normalize.processes import normalize_processes
from raptorscope.normalize.quarantine import normalize_quarantine

RULES = load_rules("detections/sigma")
HOST = {"name": "h", "os": {"type": "macos"}}


def _titles(docs):
    return {a["title"] for a in run_rules(docs, RULES)}


# ---- quarantine: real QuarantineEventsV2 has no filename, only the data URL ----
def test_quarantine_fires_on_url_only_real_schema():
    rows = [{
        "LSQuarantineTimeStamp": "2026-07-02T21:03:55Z",
        "LSQuarantineAgentName": "Google Chrome",
        "LSQuarantineDataURLString": "http://45.9.148.99/Invoice.pdf.command",
    }]
    docs = normalize_quarantine(rows, HOST)
    assert not docs[0].get("file", {}).get("name")  # no filename on real data
    assert "macOS quarantined executable or script downloaded" in _titles(docs)


def test_quarantine_benign_url_stays_silent():
    rows = [{"LSQuarantineDataURLString": "https://download.mozilla.org/firefox/Firefox.dmg"}]
    assert "macOS quarantined executable or script downloaded" not in _titles(
        normalize_quarantine(rows, HOST)
    )


# ---- process: fire on trusted:false, silent on unknown-signature and dev paths ----
_UNSIGNED = "macOS unsigned or untrusted process running"


def test_process_fires_on_untrusted_signature():
    rows = [{"Pid": 501, "Name": "helper", "Exe": "/private/tmp/x",
             "CommandLine": "/private/tmp/x",
             "CodeSignature": {"Exists": True, "Trusted": False}}]
    assert _UNSIGNED in _titles(normalize_processes(rows, HOST))


def test_process_dev_path_is_filtered():
    rows = [{"Pid": 502, "Name": "mytool", "Exe": "/opt/homebrew/bin/mytool",
             "CommandLine": "/opt/homebrew/bin/mytool",
             "CodeSignature": {"Exists": False, "Trusted": False}}]
    assert _UNSIGNED not in _titles(normalize_processes(rows, HOST))


def test_process_unknown_signature_never_false_fires():
    # stock Pslist: only a Hash, no signature -> the rule must NOT fire
    rows = [{"Pid": 503, "Name": "x", "Exe": "/usr/bin/x", "CommandLine": "/usr/bin/x",
             "Hash": {"SHA256": "abc"}}]
    assert _UNSIGNED not in _titles(normalize_processes(rows, HOST))
