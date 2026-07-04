# SPDX-License-Identifier: GPL-3.0-or-later
"""Tier-2 persistence-signature rules: fire on signature-enriched Autoruns rows
(MacOS.Raptorscope.SignedAutoruns) and stay silent on trusted / unknown-signature
rows (stock Autoruns, which never false-fires)."""
from raptorscope.detect.evaluate import load_rules, run_rules
from raptorscope.normalize.autoruns import normalize_autoruns

RULES = load_rules("detections/sigma")
HOST = {"name": "h", "os": {"type": "macos"}}


def _titles(rows):
    return {a["title"] for a in run_rules(normalize_autoruns(rows, HOST), RULES)}


_LAUNCHD = "macOS launch agent or daemon with an untrusted code signature"
_HIDDEN = "macOS hidden and unsigned login item"


def test_untrusted_launchd_fires_on_enriched_row():
    rows = [{
        "Source": "LaunchDaemons",
        "OSPath": "/Library/LaunchDaemons/com.evil.helper.plist",
        "Mtime": "2026-07-02T00:00:00Z",
        "LaunchdConfig": {"Label": "com.evil.helper", "Program": "/usr/local/evil"},
        "CodeSignature": {"Exists": False, "Trusted": False},
    }]
    assert _LAUNCHD in _titles(rows)


def test_untrusted_launchd_silent_on_trusted():
    rows = [{
        "Source": "LaunchDaemons",
        "OSPath": "/Library/LaunchDaemons/com.docker.helper.plist",
        "Mtime": "2026-07-02T00:00:00Z",
        "LaunchdConfig": {"Label": "com.docker.helper", "Program": "/Applications/Docker.app/x"},
        "CodeSignature": {"Exists": True, "Trusted": True, "SubjectName": "Developer ID: Docker"},
    }]
    assert _LAUNCHD not in _titles(rows)


def test_untrusted_launchd_silent_without_signature():
    # stock Autoruns (Hash only, no CodeSignature) -> never false-fires
    rows = [{
        "Source": "LaunchDaemons",
        "OSPath": "/Library/LaunchDaemons/com.x.plist",
        "Mtime": "2026-07-02T00:00:00Z",
        "LaunchdConfig": {"Label": "com.x", "Program": "/usr/local/x"},
        "Hash": {"SHA256": "abc"},
    }]
    assert _LAUNCHD not in _titles(rows)


def test_hidden_unsigned_login_needs_both_hidden_and_untrusted():
    hidden_unsigned = [{
        "Source": "Sandboxed Loginitems",
        "OSPath": "/Users/Shared/.x/Bad.app",
        "Mtime": "2026-07-02T00:00:00Z",
        "LoginItemConfig": {"Label": "Bad"},
        "Hidden": True,
        "CodeSignature": {"Exists": False, "Trusted": False},
    }]
    assert _HIDDEN in _titles(hidden_unsigned)

    # hidden but validly signed -> the AND-combo suppresses the FP
    hidden_signed = dict(hidden_unsigned[0])
    hidden_signed["CodeSignature"] = {"Exists": True, "Trusted": True}
    assert _HIDDEN not in _titles([hidden_signed])
