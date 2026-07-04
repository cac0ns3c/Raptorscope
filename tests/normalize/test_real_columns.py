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
