# Detection coverage

Paired Sigma detections shipped with Raptorscope, with their ECS dataset,
severity, and mapped MITRE ATT&CK techniques. Generated from `detections/sigma/`.

**15 rules** across 5 datasets.

| Rule | Dataset | Level | MITRE |
|------|---------|-------|-------|
| macOS unsigned application installed outside /Applications | `macos.inventory` | medium | T1543.001 |
| macOS BTM persistence item from suspicious path | `macos.persistence` | high | T1543.001 |
| macOS cron/periodic job runs a suspicious command | `macos.persistence` | high | T1053.003 |
| macOS login item from suspicious path | `macos.persistence` | high | T1547.015 |
| macOS persistence item runs a shell download one-liner | `macos.persistence` | high | T1059.004 |
| macOS persistence masquerading as an Apple label | `macos.persistence` | high | T1036.005 |
| macOS persistence program in suspicious path | `macos.persistence` | high | T1543 |
| macOS unsigned configuration profile installed | `macos.persistence` | medium | T1176 |
| macOS process invoking a network download or beacon | `macos.process` | high | T1105 |
| macOS process running from a suspicious path | `macos.process` | high | T1059 |
| macOS unsigned process running | `macos.process` | medium | T1036 |
| macOS quarantined executable or script downloaded | `macos.quarantine` | medium | T1566.001 |
| macOS quarantined file downloaded over cleartext HTTP | `macos.quarantine` | medium | T1189 |
| macOS TCC grant to a path-based (non-bundle) client | `macos.tcc` | medium | T1548 |
| macOS sensitive TCC grant to a non-Apple client | `macos.tcc` | high | T1548 |
