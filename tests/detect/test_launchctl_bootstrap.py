# SPDX-License-Identifier: GPL-3.0-or-later
"""launchctl bootstrap/load persistence activation: the rule fires when a plist is
loaded from a world-writable staging path (/tmp, /private/tmp, /Users/Shared) and
stays silent on the everyday-benign launchctl callers the adversarial FP hunt
turned up — brew services, pkg postinstall, MDM, dotfiles login, Xcode."""
from raptorscope.detect.evaluate import load_rules, run_rules
from raptorscope.normalize.processes import normalize_processes

RULES = load_rules("detections/sigma")
HOST = {"name": "h", "os": {"type": "macos"}}
_LC = "macOS launchd persistence activated via launchctl from a world-writable path"


def _titles(cmd):
    row = {"Pid": 9, "Name": cmd.split()[0], "Exe": "/bin/launchctl", "CommandLine": cmd}
    return {a["title"] for a in run_rules(normalize_processes([row], HOST), RULES)}


# --- fires: persistence activated straight out of a staging directory ---
def test_fires_bootstrap_gui_from_tmp():
    assert _LC in _titles("launchctl bootstrap gui/501 /tmp/com.evil.agent.plist")


def test_fires_bootstrap_system_from_users_shared():
    assert _LC in _titles("launchctl bootstrap system /Users/Shared/com.evil.daemon.plist")


def test_fires_legacy_load_w_from_private_tmp():
    assert _LC in _titles("launchctl load -w /private/tmp/com.evil.agent.plist")


# --- silent: the adversarial benign FP hunt (5+ real launchctl callers) ---
def test_silent_brew_services():
    # Homebrew `brew services start` bootstraps from ~/Library/LaunchAgents
    assert _LC not in _titles(
        "/opt/homebrew/bin/launchctl bootstrap gui/501 "
        "/Users/dev/Library/LaunchAgents/homebrew.mxcl.redis.plist"
    )


def test_silent_installer_postinstall_launchdaemons():
    # pkg postinstall loading a signed daemon from the canonical location
    assert _LC not in _titles(
        "launchctl load -w /Library/LaunchDaemons/com.vendor.helper.plist"
    )


def test_silent_mdm_managed_daemon():
    # MDM bootstrapping a managed daemon into the system domain
    assert _LC not in _titles(
        "launchctl bootstrap system /Library/LaunchDaemons/com.jamf.management.daemon.plist"
    )


def test_silent_dotfiles_login_agent():
    # a user's login script re-loading their own LaunchAgent
    assert _LC not in _titles(
        "launchctl load -w /Users/dev/Library/LaunchAgents/com.user.dotfiles.plist"
    )


def test_silent_xcode_developer_agent():
    # Xcode / developer tooling under ~/Library/Developer
    assert _LC not in _titles(
        "launchctl bootstrap gui/501 "
        "/Users/dev/Library/Developer/CoreSimulator/com.apple.CoreSimulator.plist"
    )


def test_silent_tmpdir_per_user_temp():
    # TMPDIR ($TMPDIR = /var/folders/.../T) is NOT the literal /tmp/ we key on
    assert _LC not in _titles(
        "launchctl bootstrap gui/501 /var/folders/xy/T/com.build.agent.plist"
    )


def test_silent_unrelated_launchctl_list():
    # a plain launchctl query is not a load action
    assert _LC not in _titles("launchctl list com.apple.Safari")
