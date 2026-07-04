# Raptorscope — design spec

> Status: draft for review · Date: 2026-07-03 · License: GPL-3.0-or-later
> Working name **Raptorscope** (raptor output → a scope you look through). Changeable.

## 1. What it is

An installable **macOS DFIR analytics stack** that turns Velociraptor macOS
collection output into a normalized, detection-enriched, purpose-built triage
experience. Elasticsearch is the backend datastore/query engine; a dedicated
React/TypeScript SPA (served by a FastAPI backend) is the analyst UI.

Its guiding principle, inherited from Lyrebird: **every macOS technique the tool
surfaces ships with its paired detection, versioned together** so the signal and
the rule never drift apart.

The gap it fills: Velociraptor is the best OSS macOS collector and ELK is where
teams want the data, but the glue that makes Velociraptor's *macOS* output
actually good downstream — normalized to a common schema, correlated into a
timeline, detection-ready, and presented as an IR triage workflow — barely
exists. Generic Velociraptor→Elastic exporters treat every artifact as an
undifferentiated blob of rows.

## 2. Goals / non-goals

**Goals (v1)**
- Own a curated **macOS collection profile** (a Velociraptor artifact set) that
  can be run as an offline collector *or* as server-side hunts — same output
  either way.
- Normalize collected artifacts to **Elastic Common Schema (ECS)** via pure,
  testable per-artifact mappers.
- Ship **paired detections** authored in Sigma (source of truth), converted to
  Elastic queries, with a pairing guard preventing drift.
- Provide a **dedicated GUI** (FastAPI + React/TS SPA) for macOS triage.

**Non-goals (v1) — deliberately deferred**
- Full Unified Log ingestion (firehose), FSEvents, browser history, memory.
- Live continuous EDR-style monitoring / streaming ingest.
- Multi-analyst auth/RBAC, cross-case correlation, entity-graph views.
- Windows/Linux artifacts (macOS-only, on purpose).

## 3. Architecture

```
Collection Profile (curated Velociraptor macOS artifact set)
   ├─ build → offline collector binary ─┐
   └─ run   → server-side hunt          ─┤→ Collection-<host>.zip (JSONL rows)
                                          ▼
                    ECS Normalizer  (Python, pure per-artifact mappers)   ← the heart, UI-agnostic
                                          ▼
                    Elasticsearch  (index templates / component templates you ship)
                                          ▲   │
                                          │   ▼
                    GUI backend API  (FastAPI — queries ES, runs/serves detections)
                                          ▼
                    Dedicated GUI  (React/TypeScript SPA — macOS triage front-end)

   Sigma-authored detections → converted (sigma-cli) → run against ES → alerts surfaced in the GUI
```

**Design tenet: the core is UI-agnostic.** The collection profile, normalizer,
ES schema, and detections have no knowledge of the GUI. They ship and have
standalone value (data lands in ES; detections run) even if the GUI is
unfinished. The GUI is a consumer of stable ES indices + a query API, never a
coupling point in the data path.

## 4. Components

1. **Collection Profile** — a curated set of Velociraptor macOS artifacts,
   reusing built-in `MacOS.*` artifacts where they exist and adding custom VQL to
   fill gaps. Packaged so one profile yields either an offline collector binary
   or a server hunt. This is the collection *contract*: the artifact set defines
   exactly what the normalizer must map.

2. **ECS Normalizer** (Python) — one mapper per artifact: Velociraptor result
   rows → ECS documents. Pure functions, no I/O, fixture-testable. The heart of
   the project.

3. **Elasticsearch mappings** — index templates / component templates shipped so
   fields land correctly typed. ES is backend-only.

4. **Paired detections** — authored in **Sigma** (source of truth), converted to
   Elastic queries via `sigma-cli`, surfaced as alerts. One per macOS technique
   the normalizer exposes, enforced by a **pairing guard** (no artifact ships
   without a detection; no rule selects a dead field).

5. **GUI backend API** (FastAPI, Python) — queries ES, serves collections/cases,
   runs/serves detection results. The React SPA's sole data source.

6. **GUI frontend** (React + TypeScript SPA) — the dedicated macOS DFIR triage
   experience.

7. **CLI / orchestration** (Python) — glue: build the collector, ingest a
   collection zip, bulk-index to ES, (dev) load ES templates.

## 5. v1 scope

### 5a. macOS artifact scope (the anti-ballooning decision)
A focused set answering the macOS first-hour triage questions —
*who's persisting / what ran / what got in / what got permission*:

- **Persistence:** LaunchAgents & LaunchDaemons (plists), Login Items,
  cron/periodic, config/MDM profiles, **BTM** (BackgroundTaskManagement db).
- **Execution/process:** running process listing (+ code-signing / path context).
- **Ingress:** LSQuarantine / QuarantineEventsV2 (what was downloaded, from where).
- **Access:** TCC.db (privacy grants — camera/mic/accessibility/full-disk).
- **Inventory/context:** installed applications & packages; host/system/user
  context for ECS `host.*` / `user.*`.

Each gets a paired detection where there is a real signal (e.g., LaunchAgent
pointing at an unsigned/quarantined binary; TCC accessibility grant to a
non-Apple binary; a new BTM persistence item; a process running from a
quarantined/`/tmp` path).

### 5b. GUI scope
1. Load/select a collection (case).
2. macOS "first-hour" overview.
3. Browsable per-artifact views: persistence / processes / quarantine / TCC.
4. Unified timeline across normalized events.
5. Detection alerts surfaced, with pivot-to-evidence.

Entity graphs, cross-case correlation, multi-user/auth → v2.

## 6. Testing strategy

- **Normalizer:** TDD against captured **sample collection outputs** as fixtures
  — pure row→ECS assertions, no infra.
- **Detections:** each Sigma rule runs against a hit-fixture and a benign-fixture;
  a **pairing guard** enforces artifact↔detection coverage and rejects dead
  fields — the Lyrebird anti-drift discipline.
- **Backend API:** unit tests with a mocked/ephemeral ES; contract tests on the
  query endpoints the SPA depends on.
- **Frontend:** component/interaction tests; a small set of end-to-end smoke
  tests against a dockerized ES seeded from fixtures.
- **Integration:** dockerized ES for index-template + ingest smoke tests.

## 7. Tech stack

- **Core / normalizer / CLI / backend:** Python (FastAPI backend).
- **Datastore:** Elasticsearch (OpenSearch is a drop-in alternative if full-OSS
  licensing is preferred — same ECS docs, Sigma converts to both; noted as an
  option, not v1 commitment).
- **Detections:** Sigma + `sigma-cli` (Elastic backend).
- **Frontend:** React + TypeScript SPA.
- **Collection:** Velociraptor artifacts (VQL) + offline collector.
- **License:** GPL-3.0-or-later; SPDX header on every source file.

## 8. Proposed repo layout

```
raptorscope/
  profile/            # Velociraptor collection profile (artifact set + build config)
  src/raptorscope/
    normalize/        # per-artifact ECS mappers (the heart)
    es/               # index templates, bulk indexer
    detect/           # sigma→Elastic conversion + pairing guard (code only)
    api/              # FastAPI backend
    cli.py
  web/                # React + TypeScript SPA
  detections/sigma/   # Sigma rule YAMLs, paired per artifact (source of truth)
  tests/
  fixtures/           # captured sample Velociraptor macOS collection outputs
  docs/
```

## 9. Phasing (informs the implementation plan)

1. **Core pipeline vertical slice:** collection profile (1–2 artifacts) →
   normalizer → ES index → one paired detection. Prove the spine end-to-end.
2. **Artifact breadth:** fill out the v1 artifact set + mappers + detections.
3. **Backend API:** query endpoints the SPA needs (cases, artifact views,
   timeline, alerts).
4. **GUI:** React SPA implementing the v1 GUI scope.
5. **Packaging/docs:** collector build UX, install docs, demo on a sample case.

## 10. Scope guardrails (defensive-tool posture)

Raptorscope is a **defensive DFIR** tool: it reads and analyzes collected
evidence. It never modifies endpoints, never performs live response actions on
hosts, and the collection profile only *reads* artifacts. The offline-collector
path keeps single-host batch triage fully decoupled from any live server.

## 11. Open questions (to resolve during planning)

- Exact set of built-in Velociraptor `MacOS.*` artifacts to reuse vs. custom VQL
  to author (requires a Velociraptor spike against a real/sample macOS host).
- ECS field mapping choices where macOS artifacts have no clean ECS home
  (candidate: `raptorscope.*` namespaced fields for macOS-specific attributes).
- Sigma→Elastic conversion target (Lucene vs ES|QL vs EQL) and how alerts are
  materialized (query-on-read vs. a detection run that writes alert docs).
- Final name.
```
