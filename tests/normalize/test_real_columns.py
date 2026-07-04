# SPDX-License-Identifier: GPL-3.0-or-later
"""Normalizers accept the REAL Velociraptor column names (not just the synthetic
fixtures) for the artifacts whose real schema is confirmed. See the
real-Velociraptor validation spike note."""
from raptorscope.normalize.inventory import normalize_inventory
from raptorscope.normalize.processes import normalize_processes
from raptorscope.normalize.tcc import normalize_tcc

HOST = {"name": "h", "os": {"type": "macos"}}


def test_inventory_real_packages_columns():
    # MacOS.System.Packages: Name, Version, Path, LastModified, ObtainedFrom, SignedBy
    rows = [
        {"Name": "Slack", "Version": "4.36", "Path": "/Applications/Slack.app",
         "LastModified": "2025-04-02T07:45:00Z", "SignedBy": "Slack Technologies, Inc.",
         "ObtainedFrom": "identified_developer"},
        {"Name": "Updater", "Version": "1.0", "Path": "/Users/x/.local/Updater.app",
         "LastModified": "2026-07-01T00:00:00Z", "SignedBy": "Unsigned",
         "ObtainedFrom": "unknown"},
    ]
    docs = normalize_inventory(rows, HOST)
    by = {d["raptorscope"]["app"]["name"]: d for d in docs}
    assert by["Slack"]["@timestamp"] == "2025-04-02T07:45:00Z"
    assert by["Slack"]["raptorscope"]["app"]["signed"] is True
    assert by["Updater"]["raptorscope"]["app"]["signed"] is False


def test_tcc_real_allowed_boolean():
    # MacOS.System.TCC: Service, Client, ClientType, Allowed(bool), LastModified
    rows = [
        {"Service": "kTCCServiceAccessibility", "Client": "/Users/Shared/.a/agent",
         "ClientType": 1, "Allowed": True, "LastModified": "2026-07-02T00:00:00Z"},
        {"Service": "kTCCServiceCamera", "Client": "us.zoom.xos",
         "ClientType": 0, "Allowed": False, "LastModified": "2025-01-01T00:00:00Z"},
    ]
    docs = normalize_tcc(rows, HOST)
    allowed = {d["raptorscope"]["tcc"]["service"]: d["raptorscope"]["tcc"]["allowed"] for d in docs}
    assert allowed["kTCCServiceAccessibility"] is True
    assert allowed["kTCCServiceCamera"] is False


def test_processes_real_pslist_columns():
    # MacOS.Sys.Pslist: Pid, Ppid, Name, CommandLine, Exe, Hash, Username, CreatedTime
    rows = [
        {"Pid": 501, "Ppid": 1, "Name": "helper", "Exe": "/private/tmp/helper",
         "CommandLine": "/private/tmp/helper", "Username": "analyst",
         "CreatedTime": "2026-07-03T09:41:03Z"},
    ]
    docs = normalize_processes(rows, HOST)
    assert docs[0]["@timestamp"] == "2026-07-03T09:41:03Z"
    assert docs[0]["process"]["pid"] == 501
    assert docs[0]["process"]["executable"] == "/private/tmp/helper"


def test_config_profiles_custom_vql_columns():
    # MacOS.Raptorscope.ConfigProfiles: OSPath, PayloadIdentifier, PayloadType,
    # Signed(bool), Mtime
    from raptorscope.normalize.config_profiles import normalize_config_profiles

    rows = [{
        "OSPath": "/var/db/ConfigurationProfiles/Store/com.systemhelper.support.plist",
        "PayloadIdentifier": "com.systemhelper.support",
        "PayloadType": "com.apple.webcontent-filter",
        "Signed": False,
        "Mtime": "2026-06-28T11:47:19Z",
    }]
    doc = normalize_config_profiles(rows, HOST)[0]
    p = doc["raptorscope"]["persistence"]
    assert doc["@timestamp"] == "2026-06-28T11:47:19Z"
    assert p["type"] == "config_profile"
    assert p["label"] == "com.systemhelper.support"
    assert p["payload_type"] == "com.apple.webcontent-filter"
    assert p["signed"] is False


def test_btm_custom_vql_columns():
    # MacOS.Raptorscope.BTM: Path, ItemName, DeveloperName, Disabled(bool), Hash
    from raptorscope.normalize.btm import normalize_btm

    rows = [{
        "Path": "/private/tmp/.x/helperd",
        "ItemName": "com.apple.helperd",
        "DeveloperName": "Unknown",
        "Disabled": False,
        "Type": "agent",
        "Hash": {"SHA256": "deadbeef"},
        "Mtime": "2026-07-02T04:09:57Z",
    }]
    doc = normalize_btm(rows, HOST)[0]
    p = doc["raptorscope"]["persistence"]
    assert p["type"] == "btm"
    assert p["label"] == "com.apple.helperd"
    assert p["developer"] == "Unknown"
    assert p["run_at_load"] is True  # not disabled
    assert p["hash"] == "deadbeef"
    assert doc["process"]["executable"] == "/private/tmp/.x/helperd"
