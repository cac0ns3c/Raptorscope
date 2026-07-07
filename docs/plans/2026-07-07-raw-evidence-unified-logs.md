# Plan: raw macOS evidence ingestion — Phase 1, Unified Logs

**Status:** draft / kickoff · **Date:** 2026-07-07

## Context

[TheDFIRThing](https://github.com/JouniMi/TheDFIRThing) is a Windows raw-evidence
DFIR platform: drop EVTX + registry hives into a folder, run best-of-breed parsers
(Chainsaw, Hayabusa, Regipy), get Sigma detections + Kibana dashboards — **no agent,
no live collection**. Raptorscope is the macOS counterpart, but today it requires a
**Velociraptor collection** (agent-collected, pre-structured JSON). It cannot take
*raw* evidence off a disk image or a `sysdiagnose`.

**Goal:** give Raptorscope the same *capability class* on macOS — ingest raw forensic
evidence and run it through the existing ECS → Sigma → SPA → AI pipeline. Everything
downstream already beats Kibana dashboards; the gap is purely the front of the pipe.

### macOS ↔ Windows analogy

| TheDFIRThing (Windows) | Raptorscope-to-be (macOS) |
|---|---|
| EVTX event logs | **Unified Logs** (`.logarchive` / `tracev3`) — Phase 1 |
| Chainsaw / Hayabusa | `macos-UnifiedLogs` parse → Raptorscope Sigma |
| Registry / Regipy | raw plists + SQLite (TCC.db, QuarantineEventsV2, knowledgeC, FSEvents) — Phase 2 |
| Kibana dashboards | React SPA + AI copilot *(already have it)* |
| drop files → compose → scan | drop `.logarchive` / `sysdiagnose` / Aftermath → `ingest` — Phase 3 |

### Decisions (locked)
- **Phase 1 target:** Unified Logs (`.logarchive` / tracev3) — the macOS EVTX analog.
- **Parser:** [`macos-UnifiedLogs`](https://github.com/mandiant/macos-UnifiedLogs)
  (Rust, offline, cross-platform) — parses tracev3 on Linux/Docker without a Mac, so it
  works on disk-image evidence and fits the container model.

## Key challenge (shapes the whole design)

EVTX is **discrete structured events** (EventID + fields) — Sigma matches fields
directly. Unified Logs are **high-volume, semi-structured log messages**
(subsystem/category + a free-text `eventMessage`). So:

1. **Selection, not firehose.** A `.logarchive` is millions of lines. We ingest a
   curated set of *predicates of interest* (subsystem/category/process filters), not
   everything — the DFIR-relevant slices: process exec, TCC prompts, login window,
   `launchd`/service starts, screen-sharing, `sudo`, network extension events.
2. **Extraction, not just matching.** Detection-worthy fields (e.g. an executed path,
   a TCC service+client) often live *inside* `eventMessage` and must be regex-extracted
   into ECS during normalization — the same "reconcile against real output" discipline
   already used for TCC/BTM.

The vertical slice must prove this end-to-end on **one** predicate before we fan out.

## Architecture / integration points

```
.logarchive ──(macos-UnifiedLogs)──▶ JSONL log entries
                                        │  (selection: curated predicates)
                                        ▼
                             normalize_unifiedlog(rows, host)         ← new
                                        │  (extract fields → ECS, dataset macos.unifiedlog)
                                        ▼
                 ES (or in-memory) ──▶ Sigma engine ──▶ SPA + AI      ← existing, unchanged
```

Concrete touch points:
- **New: `src/raptorscope/evidence.py`** — `load_evidence(path)` that sniffs a
  `.logarchive` (dir) / tracev3, shells out to the `macos-UnifiedLogs` binary, applies
  the predicate selection, and returns rows + a `host` object — mirroring
  `collection.load_collection()`'s `(artifacts, host)` contract so the rest of the
  pipeline is untouched.
- **CLI: `raptorscope ingest`** — sniff the input: Velociraptor collection vs raw
  `.logarchive` (later: sysdiagnose/Aftermath). Route to the right loader. Keep one
  verb; no new UX to learn.
- **New normalizer: `normalize_unifiedlog`** in `normalize/unifiedlog.py`, registered
  in `cli._NORMALIZERS`. Maps entries → ECS (`@timestamp`, `process.*`, `user.name`,
  `event.action`, and `raptorscope.unifiedlog.{subsystem,category,message}` + extracted
  fields). Dataset `macos.unifiedlog` (exec events may *also* map to `macos.process`).
- **Detections + pairing guard** — add the new ECS fields to
  `detect/pairing.py:EMITTED_FIELDS`; ship paired Sigma rules with hit + benign
  fixtures (the guard enforces dataset↔rule coverage and rejects dead fields).
- **SPA** — add a `columns.ts` entry + dataset chip for `macos.unifiedlog` (the SPA is
  dataset-driven; timeline/alerts/search work for free once the dataset exists).
- **Docker** — bake the `macos-UnifiedLogs` binary into the API image (root Dockerfile);
  it's a static Rust binary. Keeps `make up` / `make stack` self-contained.

## Phased roadmap

- **Phase 0 — vertical slice (de-risk).** ONE predicate end-to-end: pick **TCC prompts**
  or **process exec** from a real `.logarchive`. Parser call → selection → `normalize_
  unifiedlog` → ECS → one paired Sigma rule → visible in the SPA → a regression fixture
  from real output. Proves parse + extraction + detection + UI in one thin thread.
- **Phase 1 — Unified Logs as a first-class source.** Fan out to the curated predicate
  set (exec, TCC, login window, launchd/service, sudo, screen-sharing, network
  extensions). ECS mapping + a paired detection per high-value predicate. `raptorscope
  ingest <path>.logarchive` works end-to-end. Docker image carries the parser.
- **Phase 2 — raw SQLite/plist artifacts (no Velociraptor).** Parse TCC.db,
  QuarantineEventsV2, LaunchAgents/Daemons, knowledgeC, FSEvents *from raw files* off a
  disk image. Largely **reuses existing normalizers** (TCC/quarantine/persistence) — the
  new work is the raw-file readers, not the ECS mapping.
- **Phase 3 — bundle drop-and-scan.** Ingest a whole `sysdiagnose` and/or Jamf
  **Aftermath** output as one input — fan out to the sub-parsers. This is the true
  TheDFIRThing "point at `case_data/` → scan" parity.

## Phase 0 task breakdown (the first PR)

1. Vendor/build the `macos-UnifiedLogs` CLI; confirm it parses a sample `.logarchive`
   to JSONL offline (grab a small real archive via `log collect` on this Mac for a
   fixture — no personal data committed, only shape).
2. `evidence.py`: `load_unifiedlog(path, predicates)` → rows + host.
3. `normalize/unifiedlog.py`: map + regex-extract one predicate (e.g. TCC) → ECS;
   register in `_NORMALIZERS`; add fields to `EMITTED_FIELDS`.
4. One paired Sigma rule + hit/benign fixtures under `detections/` + `fixtures/`.
5. `columns.ts` + dataset chip for `macos.unifiedlog`.
6. Tests: normalizer unit test against a real-shape fixture; pairing-guard green;
   `velociraptor`-style end-to-end not needed (this path is agentless).

## Open questions

1. **Predicate catalog** — which Unified Log subsystems/categories are the Phase 1
   "must-haves"? (Proposed: exec, TCC, loginwindow, launchd, sudo, ARDAgent/screensharing,
   network extensions.) Worth a short research pass against DFIR references.
2. **Dataset modeling** — one broad `macos.unifiedlog` dataset, or route extracted
   events into existing datasets (exec→`macos.process`, TCC→`macos.tcc`)? Leaning:
   emit `macos.unifiedlog` for provenance **and** map high-value events into existing
   datasets so current detections light up.
3. **Volume/perf** — selection at parse time (predicate filter) vs post-parse; cap +
   `log()` what's dropped so we never silently truncate evidence.
4. **Fixture sourcing** — a scrubbed real `.logarchive` slice for tests without
   committing host data (same guardrail as the live-capture validation doc).

## Verification

- Phase 0: `raptorscope ingest <sample>.logarchive` → the TCC-prompt detection fires in
  the SPA on real-shape data; regression fixture green; pairing guard green; full suite
  (Python + web) unbroken.
- Each later phase: at least one paired detection validated against a real-shape fixture,
  and the new source visible end-to-end in the running app (`make up`).
