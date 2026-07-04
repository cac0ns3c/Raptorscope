# Raptorscope Artifact Breadth (Phase 2) Implementation Plan

**Goal:** Fill out the v1 macOS artifact set behind the Phase-1 spine. Every new
artifact ships the same three things Phase 1 proved once: a captured fixture, a
pure ECS mapper, and a paired Sigma detection guarded against drift. At the end,
the CLI ingests a full multi-artifact collection and every dataset is paired.

**Spec reference:** design spec §5a (macOS artifact scope). This plan is the
build cycle for phasing step 2.

**Architecture:** Extend the existing pure-Python core. New per-artifact mappers
live beside `normalize/launch_items.py`, reusing `ecs_base`. The persistence
family (login items, cron/periodic, config profiles, BTM) shares the
`macos.persistence` dataset, discriminated by `raptorscope.persistence.type`
(the Phase-1 pattern). Execution, ingress, access, and inventory each get their
own dataset. Every dataset gets ≥1 paired Sigma rule; `check_pairing` is extended
to cover the whole set and to reject dead fields.

**Tech stack:** unchanged (Python 3.10+, `pysigma` + Elastic backend, `pytest`).

## Global Constraints

- Same as Phase 1: SPDX header on every source file; GPL-3.0-or-later; DCO
  sign-off (`git commit -s`); ECS target with `raptorscope.*` for macOS-only
  fields; Sigma YAMLs are the detection source of truth; unit tests take no live
  infra.
- **Fixtures are `SYNTHETIC`** (no Velociraptor binary / live Mac in this
  environment), hand-authored from each artifact's documented column schema and
  marked SYNTHETIC in `docs/spikes/`. Tests bind to the fixture field names.
- New runtime deps (none expected) go in both `pyproject.toml` and
  `requirements.txt`.

## Dataset / discriminator model

| Dataset            | Artifact(s)                              | Discriminator                       |
|--------------------|------------------------------------------|-------------------------------------|
| `macos.persistence`| launch items (done), login items, cron/periodic, config profiles, BTM | `raptorscope.persistence.type` = `launch_agent`/`launch_daemon`/`login_item`/`cron`/`config_profile`/`btm` |
| `macos.process`    | running processes                        | —                                   |
| `macos.quarantine` | LSQuarantine / QuarantineEventsV2        | —                                   |
| `macos.tcc`        | TCC.db privacy grants                    | —                                   |
| `macos.inventory`  | installed applications                   | —                                   |

Host/user context is **enrichment**, not an event dataset: a `host.json` in the
collection is merged into every doc's `host.*`/`user.*` (extended in Task 9). It
has no detection and is exempt from the pairing guard.

---

### Task 1: Login Items (persistence)

- Fixture `fixtures/velociraptor/login_items.raw.json` + spike note. Artifact:
  `MacOS.System.LoginItems`. Columns: `Name`, `Path`, `User`, `Program`,
  `Hidden`, `Mtime`.
- `normalize/login_items.py` → `normalize_login_items(rows, host)`: `macos.persistence`,
  `persistence.type="login_item"`, `file.path`=Path, `process.executable`=Program/Path,
  label=Name, plus `user.name`=User.
- Detection `detections/sigma/macos_persistence_login_item_suspicious.yml`
  (`event.dataset: macos.persistence`, `raptorscope.persistence.type: login_item`,
  `file.path|contains` staging dirs). Extend `EMITTED_FIELDS`.
- Tests: `tests/normalize/test_login_items.py` (row→doc, type=login_item,
  user.name), and the rule converts.

### Task 2: cron / periodic (persistence)

- Fixture `cron_items.raw.json` + note. Artifact: `MacOS.System.Crontab`. Columns:
  `User`, `Command`, `Schedule`, `Path` (crontab/periodic file).
- `normalize/cron.py` → `normalize_cron(rows, host)`: `persistence.type="cron"`,
  `process.command_line`=Command, `file.path`=Path, `user.name`=User,
  `raptorscope.persistence.schedule`=Schedule.
- Detection `macos_persistence_cron_suspicious_command.yml`
  (`process.command_line|contains`: `curl`, `wget`, `base64`, `/tmp/`).
- Tests mirror Task 1.

### Task 3: Config / MDM profiles (persistence)

- Fixture `config_profiles.raw.json` + note. Artifact: `MacOS.System.Profiles`.
  Columns: `ProfileIdentifier`, `ProfileDisplayName`, `PayloadType`,
  `PayloadIdentifier`, `InstallDate`, `SignerCN` (nullable), `Path`.
- `normalize/config_profiles.py` → `persistence.type="config_profile"`,
  label=ProfileIdentifier, `raptorscope.persistence.payload_type`=PayloadType,
  `process.code_signature.subject_name`=SignerCN (`trusted`= SignerCN is not null).
- Detection `macos_persistence_config_profile_unsigned.yml` — a persistence
  profile whose payload is a known-risky type and is unsigned.
- Tests mirror.

### Task 4: BTM — Background Task Management (persistence)

- Fixture `btm_items.raw.json` + note. Artifact:
  `MacOS.System.BackgroundTaskManagement`. Columns: `UUID`, `Name`, `Developer`,
  `Executable`, `Type` (`agent`/`daemon`/`login_item`), `Enabled`, `Signature`.
- `normalize/btm.py` → `persistence.type="btm"`, `process.executable`=Executable,
  label=Name, `raptorscope.persistence.btm_type`=Type,
  `raptorscope.persistence.developer`=Developer.
- Detection `macos_persistence_btm_unsigned.yml` — BTM item, unsigned / dev
  "Unknown", executable in a staging dir.
- Tests mirror.

### Task 5: Processes (`macos.process`)

- Fixture `processes.raw.json` + note. Artifact: `MacOS.System.Processes`.
  Columns: `Pid`, `Ppid`, `Name`, `Exe`, `CommandLine`, `Username`, `Mtime`,
  `CodeSignature`.
- `normalize/processes.py` → dataset `macos.process`, `event.category=["process"]`,
  `event.type=["info"]`: `process.pid`, `process.parent.pid`,
  `process.name`, `process.executable`=Exe, `process.command_line`,
  `process.code_signature.*`, `user.name`=Username, `file.path`=Exe.
- Detection `macos_process_suspicious_path.yml` — process running from
  `/tmp`, `/private/tmp`, `/Users/Shared`, or unsigned.
- Tests: `tests/normalize/test_processes.py`.

### Task 6: Quarantine (`macos.quarantine`)

- Fixture `quarantine.raw.json` + note. Artifact: `MacOS.System.QuarantineEvents`.
  Columns: `LSQuarantineTimeStamp`, `LSQuarantineAgentName`,
  `LSQuarantineDataURLString`, `LSQuarantineOriginURLString`,
  `LSQuarantineSenderName`, `Path` (resulting file).
- `normalize/quarantine.py` → dataset `macos.quarantine`,
  `event.category=["file"]`, `event.type=["creation"]`: `url.full`=DataURL,
  `url.original`=OriginURL, `process.name`=AgentName, `file.path`=Path,
  `raptorscope.quarantine.sender`=SenderName.
- Detection `macos_quarantine_executable_from_web.yml` — a quarantined file with
  an executable extension / suspicious origin host.
- Tests: `tests/normalize/test_quarantine.py`.

### Task 7: TCC privacy grants (`macos.tcc`)

- Fixture `tcc.raw.json` + note. Artifact: `MacOS.System.TCC`. Columns:
  `Service`, `Client`, `ClientType`, `AuthValue` (0/2), `LastModified`, `Path`.
- `normalize/tcc.py` → dataset `macos.tcc`, `event.category=["configuration"]`:
  `raptorscope.tcc.service`, `raptorscope.tcc.client`,
  `raptorscope.tcc.allowed` (bool from AuthValue), `file.path`=Path,
  `process.executable`=Client path when present.
- Detection `macos_tcc_sensitive_grant_non_apple.yml` — a grant for
  accessibility / full-disk / input-monitoring to a non-`com.apple.*` client that
  is allowed.
- Tests: `tests/normalize/test_tcc.py`.

### Task 8: Installed applications inventory (`macos.inventory`)

- Fixture `installed_apps.raw.json` + note. Artifact: `MacOS.System.Packages`.
  Columns: `Name`, `BundleIdentifier`, `Version`, `Path`, `SignerCN`, `Mtime`.
- `normalize/inventory.py` → dataset `macos.inventory`,
  `event.category=["package"]`, `event.type=["info"]`: `file.path`=Path,
  `raptorscope.app.name`/`.bundle_id`/`.version`,
  `process.code_signature.subject_name`/`.trusted`.
- Detection `macos_inventory_unsigned_app_outside_applications.yml` — an app
  installed outside `/Applications` that is unsigned.
- Tests: `tests/normalize/test_inventory.py`.

### Task 9: Wire-up, host/user context, full-coverage guard

- **Host/user enrichment:** extend `load_collection`/`ingest` so `host.json` may
  carry `user` context; add helper `enrich_host` if needed. No new dataset.
- **CLI registry:** register all new normalizers in `cli._NORMALIZERS` keyed by
  their collection json stem (`login_items`, `cron_items`, `config_profiles`,
  `btm_items`, `processes`, `quarantine`, `tcc`, `installed_apps`).
- **Pairing guard:** add `ALL_DATASETS` set and a test asserting
  `check_pairing(ALL_DATASETS, "detections/sigma") == []`. Ensure `EMITTED_FIELDS`
  covers every field selected by any rule.
- **ES template:** add keyword/typed mappings for the new fields
  (`process.pid`, `process.parent.pid`, `process.name`, `url.full`,
  `url.original`, `user.name`, `raptorscope.tcc.*`, `raptorscope.app.*`,
  `raptorscope.quarantine.*`, new `persistence.*`).
- **CLI e2e:** a test that ingests a temp collection dir containing all artifacts
  and asserts the total doc count and that at least one doc per dataset is
  produced.
- Update `README.md` with the artifact coverage table.

Commit per task with the plan's `feat(...)` convention.

## Self-review notes

- **Spec coverage:** Tasks 1–8 map every artifact in spec §5a; Task 9 adds
  host/user context and closes the pairing guard over the full set.
- **Anti-drift:** every new dataset is forced to have a paired rule by the Task 9
  full-coverage test; dead-field check extends automatically as `EMITTED_FIELDS`
  grows.
- **UI-agnostic:** still no GUI/backend — Phase 3+ remain deferred.
