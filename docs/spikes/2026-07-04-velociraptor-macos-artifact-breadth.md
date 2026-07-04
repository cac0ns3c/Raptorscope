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
