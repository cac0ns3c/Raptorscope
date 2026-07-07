# MITRE ATT&CK coverage map (macOS)

How Raptorscope's detections map onto the ATT&CK for macOS matrix, and — honestly —
what is **reachable** from the evidence we collect versus what is not.

- **Navigator layer:** `detections/mitre-navigator-layer.json` (load into
  [mitre-attack.github.io/attack-navigator](https://mitre-attack.github.io/attack-navigator/)).
- **Per-rule technique table:** `detections/COVERAGE.md`.

## What we can and cannot see

Every rule is built on one of seven ECS datasets derived from a Velociraptor
collection or raw disk evidence: **process** (pslist — argv, exe, signature, user),
**persistence** (launchd/cron/BTM/login-items/config-profiles), **tcc**,
**quarantine**, **inventory** (installed apps), **network** (netstat snapshot), and
**unifiedlog** (TCC + authorization events). That is *point-in-time host state and
argv*, not a live EDR event stream.

So techniques that require **memory, API-call, or kernel telemetry** — process
injection internals (T1055.x beyond argv), in-memory-only execution (T1620),
exploitation (T1068/T1203/T1211/T1212), API-based credential theft, live AiTM
(T1557) — are **out of scope by construction** and are marked N/A below rather than
faked. Reconnaissance (TA0043) and Resource Development (TA0042) are off-host and
also N/A. This map covers **TA0001–TA0011 + TA0040**.

Legend: ✅ covered · 🎯 detectable gap (this pass fills it) · ⚪ out of scope (telemetry we don't collect).

## Coverage by tactic

> All 12 in-scope tactics are now populated (140 rules, 104 techniques). The "THIN/EMPTY" notes below are historical — see the Status section at the end for final counts.

### Execution (TA0002)
✅ T1059.002/.004/.006 (AppleScript/shell/Python) · T1204.001/.002 (user execution) ·
T1053.003 (cron) · T1559 (IPC/AppleEvents) · T1569.001 (launchctl) · T1497.001 (VM check)
🎯 T1059.007 (JXA via `osascript -l JavaScript`)
⚪ T1203/T1211 (exploitation), T1648 (serverless), T1204.003 (malicious image)

### Persistence (TA0003)
✅ T1543.001/.004 (launchd) · T1547.006 (kext) · T1547.015 (login items) ·
T1053.003 (cron) · T1098.004 (SSH keys) · T1176 (profiles) · T1554 (trojaned binary) ·
T1036.005 (masquerade label)
🎯 T1037.002 (login/logout hooks via `defaults write … LoginHook`) ·
T1546.004 (shell rc `.zshrc`/`.bash_profile` write) · T1547.011 (plist mod)
⚪ T1546.014 (Emond, removed), firmware-level persistence

### Privilege Escalation (TA0004)
✅ T1548.001/.003/.006 (setuid/sudo/TCC) · T1574.006 (DYLD injection) ·
T1055 (argv-visible injection) · T1543 (service)
🎯 T1548.004 (`security authorizationdb`/AuthExecuteWithPrivileges argv)
⚪ T1068 (exploitation for privesc)

### Defense Evasion (TA0005)
✅ T1070/.003/.006 (log+history clear, timestomp) · T1553.001 (Gatekeeper bypass) ·
T1562.001/.004 (disable tools/firewall) · T1222.002 (chmod) · T1564.001 (hidden files) ·
T1036.001/.005/.008 (masquerade) · T1140 (deobfuscate) · T1548.006 (TCC manipulation)
🎯 T1553.004 (install rogue root CA via `security add-trusted-cert`) ·
T1070.004 (secure file deletion `srm`/`rm -P`) · T1112 (defaults write to modify settings)
⚪ T1027.x on-disk entropy analysis, T1620 (reflective load)

### Credential Access (TA0006)
✅ T1003/.008 (keychain/passwd) · T1552.001/.004 (creds in files/keys) ·
T1555/.001/.003 (keychain/browser) · T1056.001/.002 (input/GUI prompt) · T1539 (cookies)
🎯 T1040 (network sniffing `tcpdump`) · T1552.003 (bash history creds)
⚪ T1110 (brute force), T1557 (AiTM), API-based cred theft

### Discovery (TA0007)  ← THIN (5 rules)
✅ T1082 (system info) · T1087.001 (accounts) · T1497.001 (VM) · T1518.001 (security sw)
🎯 T1057 (process) · T1016 (network config) · T1049 (network connections) ·
T1033 (owner/user) · T1007 (services) · T1069.001 (local groups) · T1518 (software) ·
T1201 (password policy) · T1217 (browser info) · T1083 (files/dirs)
⚪ T1046 (network service scanning — active), T1580 (cloud)

### Lateral Movement (TA0008)  ← THIN (2 rules)
✅ T1021.001 (VNC) · T1021.004 (SSH)
🎯 T1021.002 (SMB `mount_smbfs`/`smbutil`) · T1021.005 (enable ARD/Screen Sharing) ·
T1570 (lateral tool transfer scp/rsync)
⚪ T1563 (session hijack), T1550 (alternate auth material)

### Collection (TA0009)
✅ T1005 (local data) · T1056.001 (keylog) · T1113 (screen capture) · T1115 (clipboard) ·
T1123 (audio) · T1125 (video) · T1560.001 (archive)
🎯 T1119 (automated collection) · T1114 (local email `~/Library/Mail`)
⚪ T1213 (SaaS repos), T1039 (network share — no share telemetry)

### Command and Control (TA0011)
✅ T1071 (app-layer) · T1090/.003 (proxy/Tor) · T1095 (non-app protocol) ·
T1102 (web service) · T1105 (ingress transfer) · T1571 (non-standard port)
🎯 T1219 (remote access software — TeamViewer/AnyDesk/RustDesk) · T1572 (protocol tunneling ssh -L/-D)
⚪ T1573 (encrypted channel — needs payload), T1568 (DGA)

### Exfiltration (TA0010)  ← THIN (1 rule)
✅ T1041 (exfil over C2 — curl upload)
🎯 T1567.002 (exfil to cloud storage `rclone`/aws s3 cp) · T1048 (alt protocol) ·
T1052.001 (USB `/Volumes` copy)
⚪ T1029 (scheduled transfer — timing), T1011 (other medium)

### Impact (TA0040)  ← EMPTY (0 rules)
🎯 T1485 (data destruction `rm -rf`/`diskutil eraseDisk`) ·
T1486 (data encrypted / ransomware `openssl enc` mass) ·
T1490 (inhibit recovery — `tmutil deletelocalsnapshots`) ·
T1496 (resource hijacking / cryptomining `xmrig`) ·
T1489 (service stop) · T1529 (shutdown/reboot)
⚪ T1491 (defacement), T1561 (disk wipe at firmware level)

### Initial Access (TA0001)
✅ T1566.001/.002 (spearphishing attachment/link via quarantine) · T1204 (user execution)
🎯 T1091 (removable media `/Volumes` execution)
⚪ T1190 (exploit public app), T1195 (supply chain — needs build provenance)

## Status: every 🎯 gap closed

All 🎯 items above are now covered — **140 rules over 104 unique ATT&CK techniques,
all 12 in-scope tactics populated** (the 🎯 markers are kept for provenance; each is
now a shipped rule). Final per-tactic rule counts:

| Tactic | Rules | | Tactic | Rules |
|---|--:|---|---|--:|
| Defense Evasion | 31 | | Credential Access | 13 |
| Persistence | 29 | | Collection | 13 |
| Execution | 18 | | Impact | 6 |
| Privilege Escalation | 17 | | Lateral Movement | 5 |
| Command & Control | 14 | | Exfiltration | 4 |
| Discovery | 15 | | Initial Access | 5 |

Every rule keeps the bar: emitted-field-only, MITRE-tagged, a paired hit+benign case
proving fire/silent, and 0-divergence ES-native ↔ in-process parity. The ⚪ items
remain deliberately uncovered — claiming a technique we can't actually see from a
point-in-time host collection would be dishonest. Regenerate this map and the
Navigator layer from `detections/sigma/` whenever rules change.
