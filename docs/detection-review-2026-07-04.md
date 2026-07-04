# Raptorscope Detection Review — Consolidated Report

**Scope:** 15 shipped Sigma rules + 5 coverage-gap families. All findings below survived adversarial verification against `detect/evaluate.py`, the normalizers, `es/template.py`, the `mac-victim` samples, and the real-Velociraptor validation spike. Rejected findings are dropped. Every field cited exists in a normalizer; every Sigma feature used is supported by the engine (`|contains`/`|startswith`/`|endswith` + equality, list = OR, map = AND, `and/or/not/parens`).

---

## Executive summary

**Overall health: solid foundation, systemic real-data blind spot.** Every rule parses and evaluates correctly, all fields are real and correctly typed, and the rules fire as intended on the bundled synthetic fixtures. The defects are almost entirely **detection quality** (false-positive breadth, MITRE tagging, trivial evasions), not engine/field correctness — only two rules are `needs-work` for logic reasons and the rest are `minor-edits`. Three rules are effectively **solid as-is** (login-item, cron, quarantine-executable core logic).

The single most important cross-cutting issue is a **synthetic-vs-real field divergence**: the real Velociraptor collectors emit different columns than the synthetic fixtures. `MacOS.Sys.Pslist` emits `Hash`, **not** `CodeSignature`; `MacOS.Detection.Autoruns` emits `Hash`, **not** a signature block; `QuarantineEventsV2` has **no path/filename column**; `MacOS.System.Packages` does **not** emit `BundleIdentifier`. Several rules that look healthy on fixtures **silently never fire on real captures**.

**Top priorities (ranked):**

1. **Fix rules that are dead on real data.** `macos_process_unsigned` (keys on `code_signature.exists:false`, absent in real Pslist) and `macos_quarantine_executable_from_web` (keys on `file.name`, absent in real QuarantineEvents → pivot to `url.full|endswith`). Track the same dependency for any new `code_signature`-based persistence rule.
2. **Close the two load-bearing evasion gaps in persistence coverage.** `macos_persistence_suspicious_path` misses the dominant technique (plist in a normal dir whose *payload* is in `/tmp`) — add a `process.command_line` payload branch. `macos_persistence_apple_impersonation` blinds itself to `/Library/LaunchDaemons` (the #1 malware persistence dir) — narrow `/Library/` → `/Library/Apple/`.
3. **Systematize MITRE hygiene.** Recurring: `attack.persistence` tactic tagged with a technique that maps only to Defense-Evasion/Priv-Esc; parent techniques where a precise sub-technique exists. Standardize on `t1036.005`, `t1548.006` (TCC), `t1543.001/.004` (launchd), `t1204.002`.
4. **Tame FP breadth on the process/TCC/inventory families.** Add signature gates (`code_signature.trusted`) and Apple/system-path `filter` blocks where fields allow; expand the underspecified `falsepositives` blocks.
5. **Expand coverage into the confirmed-open surfaces** — the entire `macos.process` execution/LOLBin family (osascript, spctl/csrutil, xattr, inline interpreters, base64) is uncovered and answerable from real `process.command_line`.

---

## Per-rule fixes (confirmed findings only)

### `macos_persistence_suspicious_path.yml` — **needs-work**
| # | Type | Fix |
|---|------|-----|
| 1 | evasion-gap (high) | For launch_agent/daemon, `file.path` is the *plist* path, not the payload → a plist in `~/Library/LaunchAgents` pointing at `/tmp/evil` never fires. Add an OR'd branch: `selection_payload:` `{event.dataset: macos.persistence, process.command_line|contains: [/tmp/, /private/tmp/, /Users/Shared/]}`, `condition: selection or selection_payload`. |
| 2 | logic-error (med) | No `raptorscope.persistence.type` filter → superset of the login-item & btm rules (double-fires). Scope it: add `raptorscope.persistence.type: [launch_agent, launch_daemon]` to `selection`. |
| 3 | mitre (med) | After scoping, replace `attack.t1543` with `attack.t1543.001` + `attack.t1543.004`. |
| 4 | false-positive (med) | The `type` filter (F2) is the reliable FP reducer for `/Users/Shared/` vendor helpers. *(Correction to the raw review: btm.py DOES populate `code_signature.trusted`; only `autoruns.py` lacks signature data — so signature gating is unreliable only for autoruns-sourced rows.)* |
| 5 | quality (low) | Change `file.path|contains` → `file.path|startswith` for the three roots (kills mid-path `.../var/tmp/...` false hits); drop the redundant `/private/tmp/` entry (`/tmp/` already subsumes it). Keep `|contains` on the payload branch. *(Rejected: the "`/private/var/tmp` is uncovered" claim — `/tmp/` substring already matches it.)* |

### `macos_process_network_command.yml` — **needs-work**
| # | Type | Fix |
|---|------|-----|
| 1 | false-positive (high) | Bare `http://`/`https://` against a full process listing fires on every browser/updater/Homebrew/Apple daemon. Add `untrusted: {process.code_signature.trusted: false}`, `condition: selection and untrusted`, and drop bare `http://`/`https://` (keep `curl `/`wget `). |
| 2 | quality (med) | Description promises an untrusted/temp-path pairing the logic never encodes; `high` unjustified for bare-substring. Encode the gate (F1) or downgrade to medium. |
| 3 | evasion-gap (med) | Case-sensitive, curl/wget-only; drop the fixture-only `--beacon` literal; optionally add `osascript`, `nscurl`. |
| 4 | field-error (low) | **Real-data caveat (track, don't "fix"):** real Pslist emits `Hash`, not `CodeSignature` → both the URL match (if argv truncated to exe) *and* the proposed `trusted:false` gate go silent on real captures. Adopt F1 for fixtures/design, but flag that real efficacy needs a signing-enriched Pslist feed. |
| 5 | mitre (low) | Optionally add `attack.t1071`. Current `t1105` is correct. |

### `macos_process_unsigned.yml` — **needs-work**
| # | Type | Fix |
|---|------|-----|
| 1 | field-error (high) | `code_signature.exists` is only populated from the synthetic `CodeSignature` column; real `MacOS.Sys.Pslist` emits `Hash` → `None == false` is `false` → **the rule matches zero real documents.** Deprecate against real captures, OR enrich the process feed via a codesign custom-VQL, and keep `status: experimental` with the dependency documented. |
| 2 | false-positive (med) | No path/behavior correlation → noisy on dev tooling. Add `filter: {process.executable|startswith: [/opt/homebrew/, /usr/local/Cellar/, /usr/local/bin/]}`, `condition: selection and not filter`. |
| 3 | evasion-gap (med) | `exists:false` misses ad-hoc signing (`codesign -s -` → exists=true/trusted=false). Prefer/also key on `process.code_signature.trusted: false`. |
| 4 | mitre (low) | Drop `attack.execution` (no backing technique); change `attack.t1036` → `attack.t1036.001` (Invalid Code Signature). |
| 5 | severity (low) | Lower to `low` if the F2 filter is not added; keep `medium` if it is. |

### `macos_persistence_config_profile_unsigned.yml` — **needs-work**
| # | Type | Fix |
|---|------|-----|
| 1 | mitre (high) | `attack.t1176` (Browser/Software Extensions) is wrong for a config profile. Replace with `attack.t1547`; optionally add `attack.t1553` for the cert/trust-interception angle. |
| 2 | false-positive (high) | `signed` is derived purely from `SignerCN` presence in the Store plist; MDM-delivered profiles are stored unwrapped → `signed=false` → most legit managed profiles fire. At minimum document in `falsepositives`; better, fix the normalizer to derive signing from real profile metadata. |
| 3 | false-positive (med) | Description scopes to content-filter/proxy/cert payloads but logic ignores `payload_type`. Add `payloads: {raptorscope.persistence.payload_type|contains: [webcontent-filter, proxy, security]}`, `condition: selection and payloads` (malicious `com.apple.webcontent-filter` fixture still fires). |
| 4 | evasion-gap (med) | Self-signed `.mobileconfig` populates `SignerCN` → `signed=true` → bypass. Track a companion rule keyed on signer identity; stop hardcoding `trusted:true` in the normalizer. |

### `macos_persistence_apple_impersonation.yml` — **minor-edits**
| # | Type | Fix |
|---|------|-----|
| 1 | evasion-gap (high) | `filter_system` excludes all `/Library/`, blinding the rule to `/Library/LaunchDaemons` (top macOS-malware persistence dir). Narrow to `file.path|startswith: [/System/, /Library/Apple/]` (preserves the Rosetta `oahd` case). **Update `tests/detect/test_evaluate.py:45`, which encodes the old broad-`/Library/` behavior.** |
| 3 | evasion-gap (low) | `label|startswith com.apple.` is case-sensitive (`com.Apple.`/`com.applehelper` evade). Known limitation — document; do NOT add regex. |
| 4 | quality (low) | Fix `falsepositives`: "reuses **an** com.apple.*" → "**a** com.apple.*". Add positive tests (user-path com.apple.* fires; /System, config_profile, /Library/Apple do not). |
| 5 | mitre (low) | Optional: add `attack.t1543.001`/`.004` to back the `persistence` tactic tag. *(Rejected: excluding all `btm` rows — would suppress the demonstrated `com.apple.helperd` → /private/tmp masquerade.)* |

### `macos_persistence_btm_unsigned.yml` — **minor-edits**
| # | Type | Fix |
|---|------|-----|
| 1 | field-error (high) | id/filename say "unsigned" but there is no signing predicate. Add `signed: {process.code_signature.trusted: true}` + `condition: selection and not signed`. **Use this form, not `code_signature.exists: false`** — the real BTM VQL emits no `CodeSignature`, so signing is fixture-only today and Option B degrades gracefully to path-only on real data. |
| 2 | evasion-gap (high) | Add `- /var/tmp/` to `process.executable|contains` (substring also covers `/private/var/tmp/`). |
| 3 | mitre (med) | Rule matches all btm types; add `attack.t1543.004` + `attack.t1547.015` alongside `t1543.001`. |
| 4 | false-positive (med) | Signing gate (F1) removes signed Adobe/Logitech `/Users/Shared` helpers; name them in `falsepositives`. |
| 5 | severity (low) | Keep `high` only after the signing gate. |
| — | nit | `/private/tmp/` list entry is redundant (`/tmp/` subsumes it). |

### `macos_inventory_unsigned_app_outside_applications.yml` — **minor-edits**
| # | Type | Fix |
|---|------|-----|
| 1 | mitre (med) | Retag to `attack.defense_evasion` + `attack.t1036` + `attack.t1036.005`; remove `attack.persistence` + `attack.t1543.001` (rule never touches launchd). |
| 2 | evasion-gap (high) | `/Applications/` exemption is a blind spot (common malware drop); and any non-empty signer flips `signed=true` (self-sign bypass). Advisory/normalizer-level: harden `inventory.py` to require an Apple Developer-ID/notarization authority. |
| 3 | false-positive (med) | Broaden `falsepositives`: Homebrew Cask/ad-hoc-signed apps, `~/Applications` (Setapp), nested helper bundles under `/Library`. Optionally add `filter_library: {file.path|startswith: /Library/}` + `... and not filter_library` — **weigh against F2, they are in tension.** |
| — | *Rejected: lowering `level` to `low` — sibling `macos_process_unsigned` is `medium`.* |

### `macos_persistence_cron_suspicious_command.yml` — **minor-edits** (logic correct, MITRE correct)
| # | Type | Fix |
|---|------|-----|
| 1 | false-positive (med) | Drop `/tmp/` (matches benign log-redirect/cleanup crons; real macOS temp is `$TMPDIR`). Optionally replace with `| bash`, `| sh`, `sh -c`. |
| 2 | false-positive (med) | Replace bare `base64` with `base64 -d`, `base64 --decode`, **and `base64 -D`** (macOS BSD decode flag, case-sensitive engine). |
| 3 | evasion-gap (med) | Optionally add `osascript`, `nscurl`. Document whitespace/`$IFS` and non-curl downloader gaps. |
| 4 | severity (low) | After trimming, `high` is justified; else drop to `medium`. |

### `macos_persistence_shell_download.yml` — **minor-edits** (logic + MITRE solid)
| # | Type | Fix |
|---|------|-----|
| 1 | evasion-gap (med) | Case-sensitive matching — document; not fixable in-rule. |
| 2 | evasion-gap (low) | Optionally add `/dev/tcp/`, `osascript` (note: osascript is less low-FP than implied). |
| 3 | false-positive (med) | Expand `falsepositives`: monitoring/healthcheck cron pings (`hc-ping.com`), certbot renewal hooks. |
| 4 | false-positive (low) | Tighten `base64` → `base64 -d`/`--decode` (low priority). |
| 5 | mitre (low) | Optionally add `attack.t1105`. |

### `macos_process_suspicious_path.yml` — **minor-edits**
| # | Type | Fix |
|---|------|-----|
| 1 | mitre (med) | `attack.t1059` → `attack.t1204.002` (User Execution: Malicious File); keep `attack.execution`. |
| 2 | evasion-gap (med) | Executable-only misses interpreter-staged payloads (`bash /tmp/x.sh`). Add `selection_cmd: {event.dataset: macos.process, process.command_line|contains: [/tmp/, /Users/Shared/]}`, `condition: selection or selection_cmd`. |
| 3 | false-positive (med) | Add `filter_signed: {process.code_signature.trusted: true}`, `condition: selection and not filter_signed` (drops signed Installer/updater temp execs; degrades safely when signature absent). |
| 4 | severity (low) | Add F3 gate to justify `high`, else drop to `medium` (sibling unsigned rule is `medium`). |
| 5 | quality (low) | Drop redundant `/private/tmp/` entry. *(Rejected: adding `/private/var/tmp/` — already matched by `/tmp/`. Only genuine exec-path gap is `/var/folders/`, which needs an unsigned gate due to App Translocation.)* |

### `macos_tcc_sensitive_grant_non_apple.yml` — **minor-edits**
| # | Type | Fix |
|---|------|-----|
| 1 | false-positive (high) | Only exclusion is `com.apple.`; every 3rd-party Accessibility/FDA/Input-Monitoring app fires at `high`. TCC normalizer has no trust field to self-filter → rewrite `falsepositives` (keyboard/window managers, backup, EDR/AV, remote-support, cloud-sync) and/or downgrade (F6). |
| 2 | evasion-gap (med) | Add `kTCCServiceScreenCapture`, `kTCCServicePostEvent` to the `service` list. |
| 3 | evasion-gap (med) | `filter_apple` excludes all `com.apple.*` → blind to Apple-binary piggybacking (Terminal holds FDA in the sample). Document as known FN. |
| 4 | mitre (med) | Replace `attack.t1548` → `attack.t1548.006`; add `attack.t1056.001` + `attack.t1113`; drop `attack.persistence` (no backing technique). |
| 5 | field-error (low) | Broaden `filter_apple` to `client|startswith: [com.apple., /System/, /usr/libexec/]` to cut ClientType-1 Apple-daemon FPs. |
| 6 | severity (low) | Consider `medium` given FP breadth. |

### `macos_tcc_path_client_grant.yml` — **minor-edits**
| # | Type | Fix |
|---|------|-----|
| 1 | evasion-gap (med) | Bundling a loose binary into a `.app` (ClientType 0) evades `client_type=path`. Document; the non-Apple-service rule is the compensating control. |
| 2 | false-positive (med) | No path filter → fires on system binaries. Add `filter_system: {raptorscope.tcc.client|startswith: [/System/, /usr/, /Library/Apple/]}`, `condition: selection and not filter_system` (malicious `/Users/Shared/.helper/agent` still fires). |
| 3 | mitre (med) | `attack.t1548` → `attack.t1548.006`; replace `attack.persistence` with `attack.privilege-escalation`/`attack.defense-evasion`. |
| 4 | field-error (low) | Real `MacOS.System.TCC` confirms only `Allowed`/`User`, not `ClientType` → rule may never fire on real captures. Add a normalizer fallback deriving `client_type` from a leading `/` in `Client`. |
| 5 | quality (low) | Add a benign ClientType-1 fixture row (use `/usr/libexec/...`, which F2's filter catches — **not** `/opt/homebrew/...`) to exercise the filter. F2 must land before F5. |

### `macos_quarantine_executable_from_web.yml` — **minor-edits**
| # | Type | Fix |
|---|------|-----|
| 1 | field-error (high) | `file.name` derives from a `Path` column that `QuarantineEventsV2` does not emit → likely empty on real captures. Match `url.full|endswith` (real `LSQuarantineDataURLString` column, ends in the filename) with the same value list. Implement as a **replacement or separate OR'd block** — a second key in `selection` would AND and break it. |
| 2 | false-positive (med) | Drop `- .pkg` (every legit vendor installer is a quarantined `.pkg`); or split it to a separate `low` rule. |
| 3 | mitre (med) | `attack.t1566.001` (email attachment) → `attack.t1566.002` (link); add `attack.t1204.002`. |
| 4 | evasion-gap (low) | `.dmg`/`.zip`/`.mpkg`/extension-less evade; soften description, optionally add `.mpkg`. |
| 5 | evasion-gap (low) | Case-sensitive (`setup.PKG` evades); optionally add case variants. |
| 6 | quality (low) | Reword "directly-executable" (`.pkg`→Installer, `.sh`→editor; only `.command` is double-click-run). |

### `macos_quarantine_cleartext_http.yml` — **minor-edits**
| # | Type | Fix |
|---|------|-----|
| 2 | evasion-gap (med) | `HTTP://` casing evades. Optional OR-list `url.full|startswith: [http://, HTTP://, Http://]`. |
| 3 | mitre (med) | `attack.t1189` (Drive-by) → `attack.t1566.002` (Spearphishing Link). |
| 1 | evasion-gap (high) | Cleartext HTTP is near-dead signal; treat as low-value enrichment. Optionally add `payload: {file.name|endswith: [.command, .sh, .term, .pkg]}`, `condition: selection and payload`. |
| 4 | severity (low) | Lower to `low`. |
| 5 | false-positive (low) | Name concrete benign cases (http mirrors, internal/MDM portals, localhost/RFC1918). |

### `macos_persistence_login_item_suspicious.yml` — **solid as-is** (minor doc edits only)
Logic, fields, and MITRE (`t1547.015`) all correct; paired tests pass. Optional: (2) drop "or hidden" from the description (rule doesn't inspect `hidden`); (3) note the full overlap with `macos_persistence_suspicious_path`; (4) name concrete FP vendors. **Rejected:** the "add `/var/tmp/`" evasion finding — `/tmp/` substring already matches every `/var/tmp/` path.

---

## New detections (recommended)

Paste-ready bodies below use only real emitted fields and supported modifiers. Replace `id:` placeholders with fresh UUIDs.

### Tier 1 — real-field-safe (fire on real captures)

**Execution / LOLBin family (`macos.process`) — entire surface currently uncovered; all key on real `process.command_line`.**

```yaml
title: macOS AppleScript shell execution via osascript
id: REPLACE-WITH-UUID
status: experimental
description: >
  osascript invoked to bridge AppleScript to a shell payload ("do shell script")
  — the top macOS interpreter LOLBin, uncovered by existing process rules.
logsource:
  product: macos
  service: process
detection:
  selection:
    event.dataset: macos.process
    process.command_line|contains:
      - 'do shell script'
      - 'osascript -e'
  condition: selection
falsepositives:
  - Automation utilities (Alfred, Keyboard Maestro, BetterTouchTool) using osascript
level: medium
tags:
  - attack.execution
  - attack.t1059.002
```

```yaml
title: macOS Gatekeeper or SIP disabled via spctl/csrutil
id: REPLACE-WITH-UUID
status: experimental
description: >
  A live process argv attempting to disable Gatekeeper (spctl --master-disable)
  or SIP (csrutil disable) — a near-unambiguous defense-impair step before payload
  execution.
logsource:
  product: macos
  service: process
detection:
  selection:
    event.dataset: macos.process
    process.command_line|contains:
      - 'spctl --master-disable'
      - 'spctl --disable'
      - 'csrutil disable'
  condition: selection
falsepositives:
  - Deliberate admin/developer security-tooling changes
level: high
tags:
  - attack.defense_evasion
  - attack.t1562.001
```

```yaml
title: macOS quarantine attribute stripped via xattr
id: REPLACE-WITH-UUID
status: experimental
description: >
  An xattr process whose command line also references com.apple.quarantine is
  removing the download flag to bypass Gatekeeper on a dropped file. The two-block
  AND keeps it precise; distinct from the quarantine-DB rules (this is live execution).
logsource:
  product: macos
  service: process
detection:
  xattr:
    event.dataset: macos.process
    process.command_line|contains: 'xattr'
  quarantine:
    process.command_line|contains: 'com.apple.quarantine'
  condition: xattr and quarantine
falsepositives:
  - Developer/build tooling clearing quarantine on locally produced artifacts
level: high
tags:
  - attack.defense_evasion
  - attack.t1553.001
```

```yaml
title: macOS scripting interpreter running inline code
id: REPLACE-WITH-UUID
status: experimental
description: >
  python/ruby/perl invoked with an inline -c/-e one-liner — classic in-memory
  stager execution. (Parent/child chaining is not expressible: the processes
  normalizer emits only process.parent.pid, no parent name.)
logsource:
  product: macos
  service: process
detection:
  selection:
    event.dataset: macos.process
    process.command_line|contains:
      - 'python -c'
      - 'python3 -c'
      - 'ruby -e'
      - 'perl -e'
  condition: selection
falsepositives:
  - Developer tooling and package managers running inline interpreter snippets
level: medium
tags:
  - attack.execution
  - attack.t1059.006
```

```yaml
title: macOS base64-decoded payload execution
id: REPLACE-WITH-UUID
status: experimental
description: >
  base64 decode in a live process command line — a strong obfuscated-payload
  indicator with few benign endpoint uses. Includes the BSD -D flag (engine
  matching is case-sensitive).
logsource:
  product: macos
  service: process
detection:
  selection:
    event.dataset: macos.process
    process.command_line|contains:
      - 'base64 -d'
      - 'base64 --decode'
      - 'base64 -D'
  condition: selection
falsepositives:
  - Rare legitimate scripts decoding embedded data
level: medium
tags:
  - attack.defense_evasion
  - attack.t1140
```

**Persistence — reverse/interactive shell (`macos.process`-independent, real `process.command_line` on all persistence types):**

```yaml
title: macOS persistence item runs a reverse or interactive shell
id: REPLACE-WITH-UUID
status: experimental
description: >
  A persistence entry (launchd/cron/btm/login) whose command line opens a reverse
  or interactive shell — a distinct, very-low-FP C2 pattern disjoint from the
  network-fetch tokens in shell_download/cron_suspicious_command.
logsource:
  product: macos
  service: persistence
detection:
  selection:
    event.dataset: macos.persistence
    process.command_line|contains:
      - '/dev/tcp/'
      - 'bash -i'
      - 'sh -i'
      - 'nc -e'
      - 'ncat -e'
      - mkfifo
  condition: selection
falsepositives:
  - Rare admin diagnostic scripts
level: high
tags:
  - attack.persistence
  - attack.execution
  - attack.t1059.004
```

**TCC — extend the sensitive-service surface (real `service`/`client`/`allowed`; no `client_type` dependency):**

```yaml
title: macOS synthetic-input (PostEvent) TCC grant to a non-Apple client
id: REPLACE-WITH-UUID
status: experimental
description: >
  kTCCServicePostEvent lets a client inject synthetic keystrokes/clicks (keylogger
  companion / UI automation for credential theft). Few legitimate apps request it;
  uncovered by both existing TCC rules.
logsource:
  product: macos
  service: tcc
detection:
  selection:
    event.dataset: macos.tcc
    raptorscope.tcc.allowed: true
    raptorscope.tcc.service: kTCCServicePostEvent
  filter_apple:
    raptorscope.tcc.client|startswith: com.apple.
  condition: selection and not filter_apple
falsepositives:
  - A small number of automation/accessibility utilities
level: high
tags:
  - attack.collection
  - attack.t1056.001
```

```yaml
title: macOS Screen Recording TCC grant to a non-Apple client
id: REPLACE-WITH-UUID
status: experimental
description: >
  kTCCServiceScreenCapture allows silent display recording; absent from the
  existing sensitive-grant rule (Accessibility/FDA/ListenEvent only).
logsource:
  product: macos
  service: tcc
detection:
  selection:
    event.dataset: macos.tcc
    raptorscope.tcc.allowed: true
    raptorscope.tcc.service: kTCCServiceScreenCapture
  filter_apple:
    raptorscope.tcc.client|startswith: com.apple.
  condition: selection and not filter_apple
falsepositives:
  - Conferencing/screen-share tools (Zoom, Teams, OBS, Loom)
level: medium
tags:
  - attack.collection
  - attack.t1113
```

```yaml
title: macOS AppleEvents automation TCC grant to a non-Apple client
id: REPLACE-WITH-UUID
status: experimental
description: >
  kTCCServiceAppleEvents authorizes one process to script/drive another; abused
  for control and data theft. Higher benign volume than the other two — treat as
  a triage signal.
logsource:
  product: macos
  service: tcc
detection:
  selection:
    event.dataset: macos.tcc
    raptorscope.tcc.allowed: true
    raptorscope.tcc.service: kTCCServiceAppleEvents
  filter_apple:
    raptorscope.tcc.client|startswith: com.apple.
  condition: selection and not filter_apple
falsepositives:
  - Many mainstream productivity/automation apps request AppleEvents (real-world FP is high)
level: medium
tags:
  - attack.execution
  - attack.t1559.002
```

**Ingress provenance (`macos.quarantine`) — real `url.full` / `url.original` columns:**

```yaml
title: macOS quarantined download from a tunneling or anonymous file-sharing host
id: REPLACE-WITH-UUID
status: experimental
description: >
  Payload provenance points to ad-hoc abuse infrastructure (ngrok/cloudflared
  tunnels, anonymous one-shot file hosts) rather than a vendor site. These are
  typically HTTPS, so the cleartext-http and extension rules miss them.
logsource:
  product: macos
  service: quarantine
detection:
  selection:
    event.dataset: macos.quarantine
    url.full|contains:
      - 'ngrok.io'
      - 'trycloudflare.com'
      - 'transfer.sh'
      - 'anonfiles'
      - 'gofile.io'
      - '0x0.st'
      - 'file.io'
  condition: selection
falsepositives:
  - Occasional legitimate use of transfer.sh / tunnels for internal file sharing
level: medium
tags:
  - attack.command_and_control
  - attack.t1105
```

```yaml
title: macOS quarantined download whose origin is a URL shortener
id: REPLACE-WITH-UUID
status: experimental
description: >
  A shortened origin URL terminating in a file download obscures the true source —
  characteristic of phishing delivery. Uses url.original, which no existing rule
  inspects.
logsource:
  product: macos
  service: quarantine
detection:
  selection:
    event.dataset: macos.quarantine
    url.original|contains:
      - 'bit.ly/'
      - 'tinyurl.com/'
      - 't.co/'
      - 'goo.gl/'
      - 'is.gd/'
      - 'cutt.ly/'
      - 'rebrand.ly/'
  condition: selection
falsepositives:
  - Legitimately shared shortened links that resolve to benign downloads
level: medium
tags:
  - attack.initial_access
  - attack.t1204.001
```

**Inventory — known-bad + the `/Applications` blind spot (real `raptorscope.app.name` / `signed` / `file.path`):**

```yaml
title: Known-bad macOS adware/PUP present in installed-application inventory
id: REPLACE-WITH-UUID
status: experimental
description: >
  Installed app name matches a well-known macOS adware/PUP family — the explicit
  known-bad gap none of the current inventory rules cover.
logsource:
  product: macos
  service: inventory
detection:
  selection:
    event.dataset: macos.inventory
    raptorscope.app.name|contains:
      - Bundlore
      - Genieo
      - MacKeeper
      - Pirrit
      - Adload
      - Shlayer
      - InstallCore
      - Mughthesec
  condition: selection
falsepositives:
  - Security/analysis tooling that ships these family names as sample strings
level: high
tags:
  - attack.execution
  - attack.t1204.002
```

```yaml
title: Unsigned application installed directly in /Applications
id: REPLACE-WITH-UUID
status: experimental
description: >
  Closes the deliberate blind spot in the outside-/Applications rule: an unsigned
  bundle sitting IN /Applications is never flagged today.
logsource:
  product: macos
  service: inventory
detection:
  selection:
    event.dataset: macos.inventory
    raptorscope.app.signed: false
    file.path|startswith: /Applications/
  condition: selection
falsepositives:
  - Portable/developer builds dragged into /Applications
level: medium
tags:
  - attack.defense_evasion
  - attack.t1553.001
```

### Tier 2 — verified logic, but fixture-only until collectors are extended (adopt, ship with the FN caveat documented)

These are answerable from emitted fields but the **real** collectors do not populate the signature/payload columns yet, so they fire on synthetic fixtures and stay silent (false-negative, not false-positive) on real captures until the VQL is extended:

- **macOS launch agent/daemon with untrusted code signature** (`T1543.001/.004`) — `raptorscope.persistence.type: [launch_agent, launch_daemon]` + `process.code_signature.trusted: false`. Real `MacOS.Detection.Autoruns` emits `Hash`, not `CodeSignature`.
- **macOS hidden AND unsigned login item** (`T1547.015`) — `type: login_item` + `raptorscope.persistence.hidden: true` + `process.code_signature.trusted: false`. Same signature-source caveat; the AND-combo suppresses the legit-hidden-helper FP.
- **macOS running process with an invalid (present-but-untrusted) code signature** (`T1553.002`) — `macos.process` + `code_signature.exists: true` + `code_signature.trusted: false`. Catches ad-hoc/revoked/tampered that `macos_process_unsigned` misses; shares that rule's real-Pslist `Hash`-vs-`CodeSignature` dependency.
- **macOS config profile installs a traffic-interception payload** (`T1556/T1176`) — `type: config_profile` + `payload_type|contains: [webcontent-filter, vpn, dnsSettings, proxy, security.root, security.pkcs]`. Fires on the sample; real multi-payload profiles nest types under `PayloadContent[]`, so `payload_type` fidelity is unverified.

### Rejected proposals (do not build)
- *Launchd item whose Program is a bare interpreter* — no narrowing; legit agents constantly invoke `/bin/sh`/`bash`/`python3`; malicious cases already surface via command_line rules.
- *Installer/DMG over cleartext HTTP* — strict subset of the already-firing `macos_quarantine_cleartext_http` (no extension filter there).
- *Double-file-extension quarantine (`file.name|contains`)* — depends on `file.name`, absent from real `QuarantineEventsV2` (same defect as the executable_from_web F1).
- *Apple-impersonating TCC client* — redundant with the non-Apple rule and its own `filter_legit` removes the case it claims to catch; `contains: apple` matches `com.pineapple.*`.
- *Unsigned persistence executable (`macos.persistence` + `exists:false`)* & *persistence signer forges Apple* — dead on real Autoruns (no signature); the forgery variant is structurally unsatisfiable (untrusted sigs carry null `subject_name`).
- *Process from a hidden dot-dir (`executable|contains: /.`)* — matches every dev tool dir (`.cargo`, `.pyenv`, `.local`, `.vscode-server`); FP unacceptable.
- *App impersonating an Apple bundle id* — `raptorscope.app.bundle_id` not emitted by real `MacOS.System.Packages`.
- *Non-App-Store provenance* — flags all notarized third-party software; unconfirmed `ObtainedFrom` enum values.

---

## Coverage map (MITRE tactic/technique × dataset)

### `macos.persistence` (launchd / login items / cron / BTM / config profiles)
| Technique | Covered by | Status |
|---|---|---|
| T1543.001/.004 Launch Agent/Daemon | apple_impersonation, suspicious_path (after fixes), btm_unsigned | **Covered** (path/masquerade angle) |
| T1543 untrusted-signature launchd | *(new, Tier 2)* | **Gap → proposed (fixture-only until VQL adds signatures)** |
| T1547.015 Login Items | login_item_suspicious | **Covered** (staging-path only; hidden+unsigned proposed) |
| T1053.003 Cron | cron_suspicious_command | **Covered** |
| T1059.004 Shell (download) | shell_download | **Covered** |
| T1059.004 Reverse/interactive shell | *(new, Tier 1)* | **Gap → proposed** |
| T1036.005 Masquerading (Apple label/location) | apple_impersonation | **Covered** |
| Config profile unsigned | config_profile_unsigned | **Covered** (mislabeled MITRE; real-data FP risk) |
| T1556/T1176 signed interception profile | *(new, Tier 2)* | **Gap → proposed** |
| BTM masquerade | apple_impersonation (btm rows), btm_unsigned | **Covered** |
| **Open:** home-dir staging (`~/Library/*`), bundling-into-.app TCC/persistence, ad-hoc-signed persistence | — | **Open** |

### `macos.process`
| Technique | Covered by | Status |
|---|---|---|
| T1105 Ingress (curl/wget) | network_command | **Covered** (FP-heavy; needs signature gate) |
| T1204.002 / T1036 suspicious exec path | process_suspicious_path | **Covered** |
| T1036.001 unsigned process | process_unsigned | **Covered on fixtures; dead on real Pslist** |
| T1553.002 invalid (present-but-untrusted) signature | *(new, Tier 2)* | **Gap → proposed** |
| T1059.002 osascript / T1059.006 inline interpreters | *(new, Tier 1)* | **Gap → proposed** |
| T1562.001 disable Gatekeeper/SIP | *(new, Tier 1)* | **Gap → proposed** |
| T1553.001 xattr quarantine strip | *(new, Tier 1)* | **Gap → proposed** |
| T1140 base64 decode | *(new, Tier 1)* | **Gap → proposed** |
| **Open:** parent/child process chaining (normalizer emits only `process.parent.pid`), raw-IP socket C2, dropped-binary payloads | — | **Open (some structural)** |

### `macos.quarantine`
| Technique | Covered by | Status |
|---|---|---|
| T1566.001→.002 delivery (executable ext) | quarantine_executable_from_web | **Covered on fixtures; keys on synthetic `file.name` → move to `url.full`** |
| Cleartext-HTTP delivery | quarantine_cleartext_http | **Covered** (low standalone signal) |
| T1105 tunneling/anon-host provenance | *(new, Tier 1)* | **Gap → proposed** |
| T1204.001 URL-shortener origin | *(new, Tier 1)* | **Gap → proposed (`url.original` unused today)** |
| T1036.007 double extension | *(rejected — `file.name` not real)* | **Open (blocked on collector)** |
| **Open:** `.dmg`/`.zip`/extension-less payloads | — | **Open** |

### `macos.tcc`
| Technique | Covered by | Status |
|---|---|---|
| T1548.006 TCC Manipulation (Accessibility/FDA/Input-Monitoring, non-Apple) | tcc_sensitive_grant_non_apple | **Covered** (FP-heavy; MITRE needs `.006`) |
| Path-type client grant (any service) | tcc_path_client_grant | **Covered** (ClientType unconfirmed on real capture) |
| T1113 Screen Capture | *(new, Tier 1)* | **Gap → proposed** |
| T1056.001 Keylogging (PostEvent) | *(new, Tier 1)* | **Gap → proposed** |
| T1559.002 AppleEvents automation | *(new, Tier 1)* | **Gap → proposed** |
| **Open:** Apple-binary piggybacking (excluded by `filter_apple` by design) | — | **Open (structural — no trust/parent signal in TCC data)** |

### `macos.inventory`
| Technique | Covered by | Status |
|---|---|---|
| Unsigned app outside /Applications | inventory_unsigned_app_outside_applications | **Covered** (MITRE mislabeled; self-sign bypass) |
| T1553.001 unsigned app inside /Applications | *(new, Tier 1)* | **Gap → proposed** |
| T1204.002 known-bad adware/PUP name | *(new, Tier 1)* | **Gap → proposed** |
| T1036.005 Apple-bundle-id impersonation | *(rejected — `bundle_id` not real)* | **Open (blocked on collector)** |
| **Open:** provenance (`ObtainedFrom` enum unconfirmed) | — | **Open** |