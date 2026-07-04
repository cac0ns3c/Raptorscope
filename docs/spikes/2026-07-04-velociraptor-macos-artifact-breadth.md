# Spike: Velociraptor macOS artifact breadth (Phase 2)

**Status: SYNTHETIC** — no Velociraptor binary / live macOS host in this
environment. Each fixture below is hand-authored from the artifact's documented
column schema and marked SYNTHETIC. Normalizer tests bind to these column names,
so a real capture that drifts will fail loudly. Collect commands are recorded for
when a real Mac is available.

Common conventions: fixtures are JSON **arrays** (curated/trimmed from
`--format json` JSONL); `CodeSignature` objects use `Exists`/`Trusted`/
`SubjectName` (see the Phase-1 spike note); each set includes ≥1 benign row and
≥1 row the paired detection is designed to fire on.

---

## Login Items — `MacOS.System.LoginItems`

`velociraptor artifacts collect MacOS.System.LoginItems --format json`

| Column | Type | Maps to |
|--------|------|---------|
| `Name` | string | `raptorscope.persistence.label` |
| `Path` | string | `file.path`, `file.name` |
| `Program` | string | `process.executable` |
| `User` | string | `user.name` |
| `Hidden` | bool | `raptorscope.persistence.hidden` |
| `Mtime` | ISO8601 | `@timestamp` |
| `CodeSignature` | object \| null | `process.code_signature.*` |

Dataset `macos.persistence`, `persistence.type = login_item`. Fires: hidden,
unsigned `SystemUpdater.app` staged under `/Users/Shared/.updater/`.

---

## cron / periodic — `MacOS.System.Crontab`

`velociraptor artifacts collect MacOS.System.Crontab --format json`
(reads `/etc/crontab`, `/usr/lib/cron/tabs/*`, and the periodic dirs)

| Column | Type | Maps to |
|--------|------|---------|
| `User` | string | `user.name` |
| `Command` | string | `process.command_line` (`[0]` → `process.executable`) |
| `Schedule` | string | `raptorscope.persistence.schedule` |
| `Path` | string | `file.path`, `raptorscope.persistence.label` |
| `Mtime` | ISO8601 | `@timestamp` |

Dataset `macos.persistence`, `persistence.type = cron`. Fires: `analyst` crontab
running `bash -c 'curl … | bash'` every 5 minutes.

---

## config / MDM profiles — `MacOS.System.Profiles`

`velociraptor artifacts collect MacOS.System.Profiles --format json`
(`profiles -C -o stdout-xml`)

| Column | Type | Maps to |
|--------|------|---------|
| `ProfileIdentifier` | string | `raptorscope.persistence.label` |
| `PayloadType` | string | `raptorscope.persistence.payload_type` |
| `SignerCN` | string \| null | `process.code_signature.subject_name`; drives `.signed` |
| `InstallDate` | ISO8601 | `@timestamp` |
| `Path` | string | `file.path` |

Dataset `macos.persistence`, `persistence.type = config_profile`. `signed` bool
= `SignerCN is not null`. Fires: unsigned `com.systemhelper.support` web-content
filter profile.

---

## BTM — `MacOS.System.BackgroundTaskManagement`

`velociraptor artifacts collect MacOS.System.BackgroundTaskManagement --format json`
(parses the `backgroundtaskmanagementagent` db, macOS 13+)

| Column | Type | Maps to |
|--------|------|---------|
| `UUID` | string | `raptorscope.persistence.uuid` |
| `Name` | string | `raptorscope.persistence.label` |
| `Developer` | string | `raptorscope.persistence.developer` |
| `Executable` | string | `process.executable`, `file.path` |
| `Type` | `agent`/`daemon`/`login_item` | `raptorscope.persistence.btm_type` |
| `Enabled` | bool | `raptorscope.persistence.run_at_load` |
| `CodeSignature` | object \| null | `process.code_signature.*` |

Dataset `macos.persistence`, `persistence.type = btm`. Fires: unsigned
`com.apple.helperd` agent (Developer "Unknown") running from `/private/tmp/.x/`.

---

## processes — `MacOS.System.Processes`

`velociraptor artifacts collect MacOS.System.Processes --format json`

| Column | Type | Maps to |
|--------|------|---------|
| `Pid` | int | `process.pid` |
| `Ppid` | int | `process.parent.pid` |
| `Name` | string | `process.name` |
| `Exe` | string | `process.executable`, `file.path` |
| `CommandLine` | string | `process.command_line` |
| `Username` | string | `user.name` |
| `CodeSignature` | object \| null | `process.code_signature.*` |
| `Mtime` | ISO8601 | `@timestamp` |

Dataset `macos.process`, `event.category = ["process"]`. Fires: unsigned
`helper` beaconing from `/private/tmp/.cache/`.

---

## quarantine — `MacOS.System.QuarantineEvents`

`velociraptor artifacts collect MacOS.System.QuarantineEvents --format json`
(QuarantineEventsV2 db)

| Column | Type | Maps to |
|--------|------|---------|
| `LSQuarantineTimeStamp` | ISO8601 | `@timestamp` |
| `LSQuarantineAgentName` | string | `process.name` (downloading app) |
| `LSQuarantineDataURLString` | string | `url.full` |
| `LSQuarantineOriginURLString` | string | `url.original` (referrer) |
| `LSQuarantineSenderName` | string \| null | `raptorscope.quarantine.sender` |
| `Path` | string | `file.path`, `file.name` |

Dataset `macos.quarantine`, `event.category = ["file"]`. Fires:
`Invoice.pdf.command` double-extension payload downloaded from a raw-IP origin.

---

## TCC — `MacOS.System.TCC`

`velociraptor artifacts collect MacOS.System.TCC --format json`
(per-user and system `TCC.db` `access` table)

| Column | Type | Maps to |
|--------|------|---------|
| `Service` | string (`kTCCService…`) | `raptorscope.tcc.service` |
| `Client` | string | `raptorscope.tcc.client`; `process.executable` when path |
| `ClientType` | 0 (bundle id) / 1 (path) | `raptorscope.tcc.client_type` |
| `AuthValue` | 0 denied / 2 allowed | `raptorscope.tcc.allowed` (>= 2) |
| `LastModified` | ISO8601 | `@timestamp` |
| `Path` | string | `file.path` (the TCC.db) |

Dataset `macos.tcc`. Fires: `kTCCServiceAccessibility` allowed to non-Apple path
client `/Users/Shared/.helper/agent`. The rule excludes `com.apple.*` clients and
non-sensitive services (Zoom camera grant does not fire).
