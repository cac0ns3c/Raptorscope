# Detection coverage

Paired Sigma detections shipped with Raptorscope, with their ECS dataset,
severity, and mapped MITRE ATT&CK techniques. Generated from `detections/sigma/`.

**140 rules** across 7 datasets, mapping to **104 unique ATT&CK techniques**. Every rule ships a paired hit + benign fixture and is drift-guarded by `detect/pairing.py`. See `MITRE_COVERAGE.md` for the tactic map and `mitre-navigator-layer.json` for the Navigator layer.

Per dataset: `macos.inventory` 7 · `macos.network` 8 · `macos.persistence` 20 · `macos.process` 81 · `macos.quarantine` 8 · `macos.tcc` 9 · `macos.unifiedlog` 7

| Rule | Dataset | Level | MITRE |
|------|---------|-------|-------|
| macOS application bundle installed in a temporary or shared staging path | `macos.inventory` | medium | T1036.005 |
| macOS known adware or PUP family present in installed-application inventory | `macos.inventory` | high | T1204.002 |
| macOS remote-access software present in installed-application inventory | `macos.inventory` | medium | T1219 |
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
| macOS DNS tunneling / DNS-C2 tool execution | `macos.process` | high | T1071.004 |
| macOS Gatekeeper assessment rule disabled or allowlisted via spctl | `macos.process` | medium | T1562.001 |
| macOS Gatekeeper or SIP weakened via spctl or csrutil | `macos.process` | high | T1562.001 |
| macOS JavaScript for Automation (JXA) execution via osascript | `macos.process` | high | T1059.007 |
| macOS Keychain credential dumping via security dump-keychain | `macos.process` | high | T1555.001 |
| macOS LaunchAgent/LaunchDaemon plist executable modified in place | `macos.process` | high | T1547.011 |
| macOS SMB share mount / enumeration | `macos.process` | medium | T1021.002 |
| macOS SSH and cloud credential file harvest | `macos.process` | high | T1552.004, T1552.001 |
| macOS TCC privacy database tampered via sqlite3 | `macos.process` | high | T1548.006 |
| macOS account added to admin or wheel group via dseditgroup | `macos.process` | high | T1098 |
| macOS anti-forensic secure file deletion | `macos.process` | medium | T1070.004 |
| macOS authorization database weakened via security authorizationdb | `macos.process` | high | T1548 |
| macOS automated collection via find with a copy/archive action | `macos.process` | medium | T1119 |
| macOS base64-decoded payload piped to a shell or interpreter | `macos.process` | high | T1140, T1059.004 |
| macOS boot-args tampered to disable library validation or AMFI | `macos.process` | high | T1562.001 |
| macOS broad file and directory discovery | `macos.process` | medium | T1083 |
| macOS browser credential store access | `macos.process` | high | T1555.003 |
| macOS browser history and bookmark file discovery | `macos.process` | medium | T1217 |
| macOS bulk encryption of user data for impact | `macos.process` | high | T1486 |
| macOS clipboard capture via pbpaste to file or network | `macos.process` | medium | T1115 |
| macOS credential search through shell history files | `macos.process` | medium | T1552.003 |
| macOS cryptomining / resource hijacking | `macos.process` | high | T1496 |
| macOS data copied to removable / mounted volume | `macos.process` | medium | T1052.001 |
| macOS data exfiltration to cloud storage | `macos.process` | medium | T1567.002 |
| macOS data exfiltration via curl upload | `macos.process` | medium | T1041 |
| macOS destructive wipe of user data or whole volume | `macos.process` | high | T1485 |
| macOS dylib injection via DYLD_INSERT_LIBRARIES | `macos.process` | high | T1574.006 |
| macOS elevated execution requested via authorization prompt | `macos.process` | high | T1548.004 |
| macOS execute bit set on file in Downloads or Shared | `macos.process` | medium | T1222.002 |
| macOS exfiltration over alternative protocol (ftp/tftp) | `macos.process` | medium | T1048 |
| macOS fake password prompt via osascript hidden-answer dialog | `macos.process` | high | T1056.002 |
| macOS file hidden via chflags or SetFile invisible bit | `macos.process` | medium | T1564.001 |
| macOS file timestamps altered (timestomp) | `macos.process` | medium | T1070.006 |
| macOS host hardware/OS fingerprinting via system_profiler | `macos.process` | medium | T1082 |
| macOS inhibit system recovery via snapshot or Time Machine tampering | `macos.process` | high | T1490 |
| macOS installed software discovery | `macos.process` | medium | T1518 |
| macOS kernel extension loaded from a world-writable staging path | `macos.process` | high | T1547.006 |
| macOS known credential dumping tool execution | `macos.process` | high | T1555 |
| macOS lateral tool transfer over SSH (rsync/sftp push) | `macos.process` | medium | T1570 |
| macOS launchd persistence activated via launchctl from a world-writable path | `macos.process` | high | T1543.001, T1543.004 |
| macOS local account creation or admin escalation via dscl or sysadminctl | `macos.process` | high | T1136.001 |
| macOS local account enumeration via dscl/dscacheutil | `macos.process` | medium | T1087.001 |
| macOS local email store collection | `macos.process` | medium | T1114.001 |
| macOS local password hash dump via dscl ShadowHashData | `macos.process` | high | T1003 |
| macOS local permission group membership discovery | `macos.process` | medium | T1069.001 |
| macOS login keychain file raw read | `macos.process` | high | T1555.001 |
| macOS login/logout hook installed via defaults write | `macos.process` | high | T1037.002 |
| macOS network sniffing via packet capture tooling | `macos.process` | medium | T1040 |
| macOS non-interactive SSH lateral movement via sshpass or disabled host checking | `macos.process` | high | T1021.004 |
| macOS password policy discovery via pwpolicy | `macos.process` | medium | T1201 |
| macOS payload run as root via launchctl asuser 0 | `macos.process` | high | T1548 |
| macOS persistence via shell startup file modification | `macos.process` | medium | T1546.004 |
| macOS private key export via security export identities | `macos.process` | high | T1552.004 |
| macOS process discovery filtered for security or monitoring tooling | `macos.process` | high | T1057 |
| macOS process invoking a network download or beacon | `macos.process` | high | T1105 |
| macOS process running from a suspicious path | `macos.process` | high | T1204.002 |
| macOS protocol tunneling / port forwarding | `macos.process` | medium | T1572 |
| macOS quarantine attribute stripped via xattr | `macos.process` | high | T1553.001 |
| macOS remote desktop / screen sharing enabled from command line | `macos.process` | high | T1021.005 |
| macOS rogue root CA trusted via security add-trusted-cert | `macos.process` | high | T1553.004 |
| macOS screensaver password prompt disabled via defaults write | `macos.process` | medium | T1112 |
| macOS scripting interpreter executing inline code | `macos.process` | medium | T1059.004, T1059.006 |
| macOS security agent unloaded or killed | `macos.process` | high | T1562.001 |
| macOS security posture discovery (Gatekeeper/SIP/FileVault/firewall status) | `macos.process` | medium | T1518.001 |
| macOS sensitive password file access | `macos.process` | high | T1003.008 |
| macOS shell history cleared or disabled | `macos.process` | medium | T1070.003 |
| macOS silent screen capture to a file | `macos.process` | medium | T1113 |
| macOS staging of user data into an archive | `macos.process` | medium | T1560.001 |
| macOS sudoers policy tampered from the command line | `macos.process` | high | T1548.003 |
| macOS system network configuration discovery | `macos.process` | medium | T1016 |
| macOS system network connections discovery | `macos.process` | medium | T1049 |
| macOS system owner and user discovery burst | `macos.process` | medium | T1033 |
| macOS system service discovery via launchctl | `macos.process` | medium | T1007 |
| macOS system service stop via launchctl or killall | `macos.process` | medium | T1489 |
| macOS system shutdown or reboot | `macos.process` | medium | T1529 |
| macOS unified logs or diagnostics cleared | `macos.process` | high | T1070 |
| macOS unsigned binary executed from a mounted volume | `macos.process` | medium | T1091 |
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
| macOS TCC request from a binary in a world-writable/temp path (Unified Log) | `macos.unifiedlog` | high | T1059.002, T1082 |
| macOS authorization right granted to a process in a temp/world-writable path (Unified Log) | `macos.unifiedlog` | high | T1548 |
| macOS non-Apple client requested a sensitive TCC service (Unified Log) | `macos.unifiedlog` | high | T1548.006, T1056.001, T1113 |
| macOS non-system process granted a sensitive authorization right (Unified Log) | `macos.unifiedlog` | high | T1543.001, T1548 |
| macOS raw binary requested AppleEvents/keystroke-synthesis TCC service (Unified Log) | `macos.unifiedlog` | high | T1059.002, T1056.001 |
| macOS raw binary requested EndpointSecurity TCC service (Unified Log) | `macos.unifiedlog` | high | T1562.001 |
| macOS task-port / task_for_pid authorization right granted (Unified Log) | `macos.unifiedlog` | high | T1055 |
