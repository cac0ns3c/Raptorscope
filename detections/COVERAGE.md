# Detection coverage

Paired Sigma detections shipped with Raptorscope, with their ECS dataset,
severity, and mapped MITRE ATT&CK techniques. Generated from `detections/sigma/`.

**89 rules** across 7 datasets, mapping to **60 unique ATT&CK techniques**. Every rule ships a paired hit + benign fixture and is drift-guarded by `detect/pairing.py`.

Per dataset: `macos.inventory` 6 · `macos.network` 8 · `macos.persistence` 20 · `macos.process` 36 · `macos.quarantine` 8 · `macos.tcc` 9 · `macos.unifiedlog` 2

| Rule | Dataset | Level | MITRE |
|------|---------|-------|-------|
| macOS application bundle installed in a temporary or shared staging path | `macos.inventory` | medium | T1036.005 |
| macOS known adware or PUP family present in installed-application inventory | `macos.inventory` | high | T1204.002 |
| macOS unsigned application impersonating a major vendor bundle identifier | `macos.inventory` | high | T1036.005 |
| macOS unsigned application impersonating an Apple bundle identifier | `macos.inventory` | high | T1036.005 |
| macOS unsigned application installed directly in /Applications | `macos.inventory` | medium | T1553.001 |
| macOS unsigned application installed outside /Applications | `macos.inventory` | medium | T1036, T1036.005 |
| macOS UDP beacon to a backdoor/C2 remote port | `macos.network` | high | T1571 |
| macOS established connection to a backdoor/C2 remote port | `macos.network` | high | T1571 |
| macOS host listening on an RDP port | `macos.network` | high | T1021, T1021.001 |
| macOS listener bound on a common backdoor/C2 port | `macos.network` | high | T1571 |
| macOS outbound connection to a Tor or SOCKS anonymity port | `macos.network` | high | T1090, T1090.003 |
| macOS outbound connection to an IRC C2 port | `macos.network` | medium | T1071 |
| macOS shell or interpreter bound to a listening socket | `macos.network` | high | T1095, T1059.004 |
| macOS shell or interpreter with an outbound network connection | `macos.network` | high | T1095, T1059.004 |
| macOS BTM daemon registered by an unknown developer | `macos.persistence` | high | T1543.004 |
| macOS BTM item claims Apple developer from a non-system path | `macos.persistence` | high | T1036.005, T1543.004 |
| macOS BTM persistence item from suspicious path | `macos.persistence` | high | T1543.001, T1543.004, T1547.015 |
| macOS cron/periodic job executes a binary from a world-writable path | `macos.persistence` | high | T1053.003 |
| macOS cron/periodic job runs a suspicious command | `macos.persistence` | high | T1053.003 |
| macOS hidden and unsigned login item | `macos.persistence` | high | T1547.015 |
| macOS launch agent or daemon with an untrusted code signature | `macos.persistence` | high | T1543.001, T1543.004 |
| macOS login item from suspicious path | `macos.persistence` | high | T1547.015 |
| macOS login item points directly at a shell or interpreter | `macos.persistence` | high | T1547.015 |
| macOS persistence item disables system security controls | `macos.persistence` | high | T1562.001 |
| macOS persistence item dumps or queries the login keychain | `macos.persistence` | high | T1555.001 |
| macOS persistence item runs AppleScript that shells out | `macos.persistence` | high | T1059.002 |
| macOS persistence item runs a reverse or interactive shell | `macos.persistence` | high | T1059.004 |
| macOS persistence item runs a shell download one-liner | `macos.persistence` | high | T1059.004 |
| macOS persistence item runs inline scripting-interpreter code | `macos.persistence` | high | T1059.006 |
| macOS persistence item runs screencapture for surveillance | `macos.persistence` | medium | T1113 |
| macOS persistence item writes to SSH authorized_keys | `macos.persistence` | high | T1098.004 |
| macOS persistence masquerading as an Apple label | `macos.persistence` | high | T1036.005, T1543.001, T1543.004 |
| macOS persistence program in suspicious path | `macos.persistence` | high | T1543.001, T1543.004 |
| macOS unsigned configuration profile installed | `macos.persistence` | medium | T1547, T1553 |
| macOS AppleScript shell execution via osascript | `macos.process` | medium | T1059.002 |
| macOS Application Firewall disabled via socketfilterfw | `macos.process` | high | T1562.004 |
| macOS Gatekeeper assessment rule disabled or allowlisted via spctl | `macos.process` | medium | T1562.001 |
| macOS Gatekeeper or SIP weakened via spctl or csrutil | `macos.process` | high | T1562.001 |
| macOS Keychain credential dumping via security dump-keychain | `macos.process` | high | T1555.001 |
| macOS SSH and cloud credential file harvest | `macos.process` | high | T1552.004, T1552.001 |
| macOS TCC privacy database tampered via sqlite3 | `macos.process` | high | T1548.006 |
| macOS base64-decoded payload piped to a shell or interpreter | `macos.process` | high | T1140, T1059.004 |
| macOS browser credential store access | `macos.process` | high | T1555.003 |
| macOS clipboard capture via pbpaste to file or network | `macos.process` | medium | T1115 |
| macOS data exfiltration via curl upload | `macos.process` | medium | T1041 |
| macOS execute bit set on file in Downloads or Shared | `macos.process` | medium | T1222.002 |
| macOS fake password prompt via osascript hidden-answer dialog | `macos.process` | high | T1056.002 |
| macOS file hidden via chflags or SetFile invisible bit | `macos.process` | medium | T1564.001 |
| macOS file timestamps altered (timestomp) | `macos.process` | medium | T1070.006 |
| macOS host hardware/OS fingerprinting via system_profiler | `macos.process` | medium | T1082 |
| macOS known credential dumping tool execution | `macos.process` | high | T1555 |
| macOS launchd persistence activated via launchctl from a world-writable path | `macos.process` | high | T1543.001, T1543.004 |
| macOS local account creation or admin escalation via dscl or sysadminctl | `macos.process` | high | T1136.001 |
| macOS local account enumeration via dscl/dscacheutil | `macos.process` | medium | T1087.001 |
| macOS local password hash dump via dscl ShadowHashData | `macos.process` | high | T1003 |
| macOS login keychain file raw read | `macos.process` | high | T1555.001 |
| macOS private key export via security export identities | `macos.process` | high | T1552.004 |
| macOS process invoking a network download or beacon | `macos.process` | high | T1105 |
| macOS process running from a suspicious path | `macos.process` | high | T1204.002 |
| macOS quarantine attribute stripped via xattr | `macos.process` | high | T1553.001 |
| macOS scripting interpreter executing inline code | `macos.process` | medium | T1059.004, T1059.006 |
| macOS security agent unloaded or killed | `macos.process` | high | T1562.001 |
| macOS security posture discovery (Gatekeeper/SIP/FileVault/firewall status) | `macos.process` | medium | T1518.001 |
| macOS sensitive password file access | `macos.process` | high | T1003.008 |
| macOS shell history cleared or disabled | `macos.process` | medium | T1070.003 |
| macOS silent screen capture to a file | `macos.process` | medium | T1113 |
| macOS staging of user data into an archive | `macos.process` | medium | T1560.001 |
| macOS unified logs or diagnostics cleared | `macos.process` | high | T1070 |
| macOS unsigned or untrusted process running | `macos.process` | medium | T1036.001 |
| macOS virtualization/sandbox detection via ioreg vendor grep | `macos.process` | high | T1497.001 |
| macOS quarantined download delivered from a chat/file-drop CDN | `macos.quarantine` | medium | T1105, T1102 |
| macOS quarantined download from a file-extension look-alike TLD (.zip/.mov) | `macos.quarantine` | medium | T1566.002, T1105 |
| macOS quarantined download from a paste site or anonymous file host | `macos.quarantine` | medium | T1105, T1102 |
| macOS quarantined download from a tunneling or anonymous file-sharing host | `macos.quarantine` | medium | T1105 |
| macOS quarantined download whose origin URL is a link shortener | `macos.quarantine` | medium | T1566.002, T1204.001 |
| macOS quarantined download with a double-extension masquerade | `macos.quarantine` | high | T1036.008, T1204.002 |
| macOS quarantined executable or script downloaded | `macos.quarantine` | medium | T1566.002, T1204.002 |
| macOS quarantined file downloaded over cleartext HTTP | `macos.quarantine` | low | T1566.002 |
| macOS App-Management TCC grant to a non-Apple client | `macos.tcc` | medium | T1554 |
| macOS AppleEvents automation TCC grant to a non-Apple client | `macos.tcc` | medium | T1548.006, T1559 |
| macOS Camera or Microphone TCC grant to an unexpected non-Apple client | `macos.tcc` | medium | T1123, T1125 |
| macOS Screen Recording TCC grant to a non-Apple client | `macos.tcc` | medium | T1113 |
| macOS SysAdminFiles TCC grant to a non-Apple client | `macos.tcc` | high | T1548.006 |
| macOS TCC grant to a path-based (non-bundle) client | `macos.tcc` | medium | T1548.006 |
| macOS protected-folder (Desktop/Documents/Downloads) TCC grant to a non-Apple client | `macos.tcc` | medium | T1005 |
| macOS sensitive TCC grant to a non-Apple client | `macos.tcc` | high | T1548.006, T1056.001, T1113 |
| macOS synthetic-input (PostEvent) TCC grant to a non-Apple client | `macos.tcc` | high | T1056.001 |
| macOS non-Apple client requested a sensitive TCC service (Unified Log) | `macos.unifiedlog` | high | T1548.006, T1056.001, T1113 |
| macOS non-system process granted a sensitive authorization right (Unified Log) | `macos.unifiedlog` | high | T1543.001, T1548 |
