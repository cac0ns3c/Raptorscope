# Spike: Velociraptor macOS launch-item persistence output

**Status: SYNTHETIC** — This environment has no Velociraptor binary and no
separate live macOS host to run a collector against. Per Task 2, Step 2 of the
plan, the fixture (`fixtures/velociraptor/launch_items.raw.json`) is
**hand-authored from the artifact's documented column schema** rather than
captured. It is marked SYNTHETIC here. Task 3's normalizer tests bind to the
field names below, so when a real capture replaces the fixture, any drift in
column names will fail those tests loudly.

## Artifact

- **Artifact name:** `MacOS.System.LaunchServices`
  (the built-in launchd/launch-item enumerator; equivalent community artifacts:
  `MacOS.Detection.Autoruns`, `Mac.System.Plist`). It walks the standard launchd
  search paths and parses each `.plist`:
  - `/Library/LaunchDaemons/`, `/Library/LaunchAgents/`
  - `/System/Library/LaunchDaemons/`, `/System/Library/LaunchAgents/`
  - per-user `~/Library/LaunchAgents/`
- **Collect command (for a real capture, when a Mac is available):**
  ```bash
  velociraptor artifacts collect MacOS.System.LaunchServices --format json \
    > fixtures/velociraptor/launch_items.raw.json
  ```
  Note: `--format json` emits JSONL (one object per line). The trimmed fixture is
  stored as a JSON **array** (curated for tests); the collection loader / tests
  read it with `json.loads`. A real capture should be reshaped to an array (or
  the loader taught to read JSONL) when swapped in.

## Columns used downstream (the normalizer contract)

| Column            | Type            | Maps to (ECS)                              |
|-------------------|-----------------|--------------------------------------------|
| `Path`            | string          | `file.path`, `file.name`                   |
| `Label`           | string          | `raptorscope.persistence.label`            |
| `Program`         | string \| null  | `process.executable` (preferred)           |
| `ProgramArguments`| list \| null    | `process.command_line`; `[0]` is fallback executable |
| `RunAtLoad`       | bool            | `raptorscope.persistence.run_at_load`      |
| `Mtime`           | ISO8601 string  | `@timestamp`                               |
| `CodeSignature`   | object \| null  | `process.code_signature.exists/.subject_name/.trusted` |

`raptorscope.persistence.type` is derived from `Path`: `launch_agent` if the path
contains `LaunchAgents`, else `launch_daemon`.

`CodeSignature` sub-fields: `Exists` (bool), `Trusted` (bool),
`SubjectName` (string \| null), `TeamIdentifier` (string \| null).

## The four curated rows

1. **Legit LaunchDaemon** — `com.apple.softwareupdated`, has a `Program`, Apple
   code signature trusted. Baseline noise, should not fire.
2. **Legit LaunchAgent** — `com.google.keystone.agent`, uses `ProgramArguments`
   (list), Developer-ID signed. Exercises the args-join path.
3. **Malicious LaunchAgent** — `com.apple.updates` in a user's
   `~/Library/LaunchAgents`, `ProgramArguments` runs `bash -c 'curl … | bash'`,
   **unsigned** (`CodeSignature: null`). Apple-impersonating label.
4. **Malicious, suspicious path** — plist dropped in `/Users/Shared/.cache/…`,
   `Program` under `/private/tmp/…`, unsigned. This is the row the paired Sigma
   rule (`file.path|contains: /Users/Shared/`, `/private/tmp/`) is designed to
   fire on.

## Surprises / notes for future mappers

- `Program` and `ProgramArguments` are mutually-exclusive in practice: a plist
  typically has one or the other. Normalizer prefers `Program`, falls back to
  `ProgramArguments[0]`.
- `ProgramArguments` can legitimately be a single-element list or absent (`null`).
- `CodeSignature` is `null` when the target binary is unsigned or the plist has no
  resolvable program — treat absence as "not signed / unknown", not an error.
- Real Velociraptor also emits `OSPath` (kept as a redundant path source) and
  bookkeeping columns (`KeepAlive`, etc.) the normalizer currently ignores.
