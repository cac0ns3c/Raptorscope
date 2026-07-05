# SPDX-License-Identifier: GPL-3.0-or-later
"""The 5 review detections salvaged from the FP-hardened workflow: each fires on
its malicious row AND stays silent on the exact false-positive scenario the
adversarial skeptics found — proving the tightening defeats that FP."""
from raptorscope.detect.evaluate import load_rules, run_rules
from raptorscope.normalize.processes import normalize_processes
from raptorscope.normalize.quarantine import normalize_quarantine
from raptorscope.normalize.tcc import normalize_tcc

RULES = load_rules("detections/sigma")
HOST = {"name": "h", "os": {"type": "macos"}}


def _titles(norm, row):
    return {a["title"] for a in run_rules(norm([row], HOST), RULES)}


def _proc(cmd):
    return {"Pid": 9, "Name": cmd.split()[0], "Exe": "/usr/bin/x", "CommandLine": cmd}


# --- local account creation: named account fires, Nix _nixbld* stays silent ---
_ACCT = "macOS local account creation or admin escalation via dscl or sysadminctl"


def test_account_creation_fires_on_named_account():
    assert _ACCT in _titles(normalize_processes, _proc("dscl . -create /Users/backdoor UserShell /bin/bash"))


def test_account_creation_silent_on_nix_service_account():
    # the skeptics' FP: the Nix multi-user installer creates 32 _nixbld* users
    assert _ACCT not in _titles(normalize_processes, _proc("dscl . -create /Users/_nixbld7 UniqueID 357"))


# --- keychain dump: dump-keychain fires, single-secret lookup stays silent ---
_KC = "macOS Keychain credential dumping via security dump-keychain"


def test_keychain_dump_fires():
    assert _KC in _titles(normalize_processes, _proc("security dump-keychain -d /Users/a/Library/Keychains/login.keychain-db"))


def test_keychain_dump_silent_on_single_lookup():
    assert _KC not in _titles(normalize_processes, _proc("security find-generic-password -w -s github.com"))


# --- TCC sqlite3 tamper: write-into-access fires, backup-agent substring silent ---
_SQL = "macOS TCC privacy database tampered via sqlite3"


def test_tcc_sqlite3_fires_on_write():
    cmd = 'sqlite3 /Users/a/Library/Application Support/com.apple.TCC/TCC.db "INSERT INTO access VALUES(0)"'
    assert _SQL in _titles(normalize_processes, _proc(cmd))


def test_tcc_sqlite3_silent_on_backup_agent_substring():
    # the skeptics' FP: catalog.sqlite3 + a TCC.db --include path + "update-catalog"
    cmd = '/usr/local/bin/backupd --update-catalog /var/db/catalog.sqlite3 --include "/Users/a/Library/Application Support/com.apple.TCC/TCC.db"'
    assert _SQL not in _titles(normalize_processes, _proc(cmd))


# --- SysAdminFiles TCC: non-Apple fires, XProtect under /Library/Apple silent ---
_SAF = "macOS SysAdminFiles TCC grant to a non-Apple client"


def _tcc(client, ctype):
    return {"Service": "kTCCServiceSystemPolicySysAdminFiles", "Client": client,
            "ClientType": ctype, "AuthValue": 2, "LastModified": "2026-06-15T09:12:00Z"}


def test_sysadminfiles_fires_on_non_apple():
    assert _SAF in _titles(normalize_tcc, _tcc("com.unknown.configtool", 0))


def test_sysadminfiles_silent_on_apple_xprotect():
    # the skeptics' FP: Apple XProtect Remediator under /Library/Apple (path client)
    p = "/Library/Apple/System/Library/CoreServices/XProtect.app/Contents/MacOS/XProtectRemediator"
    assert _SAF not in _titles(normalize_tcc, _tcc(p, 1))


# --- chat CDN: Discord fires, raw GitHub (removed from list) stays silent ---
_CDN = "macOS quarantined download delivered from a chat/file-drop CDN"


def test_chat_cdn_fires_on_discord():
    row = {"LSQuarantineDataURLString": "https://cdn.discordapp.com/attachments/9/5/Update.dmg"}
    assert _CDN in _titles(normalize_quarantine, row)


def test_chat_cdn_silent_on_raw_github():
    # the skeptics' FP: developers fetch scripts/assets from raw.githubusercontent daily
    row = {"LSQuarantineDataURLString": "https://raw.githubusercontent.com/org/repo/main/install.sh"}
    assert _CDN not in _titles(normalize_quarantine, row)
