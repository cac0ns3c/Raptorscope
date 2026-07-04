# Raptorscope

macOS DFIR analytics stack: Velociraptor macOS collections → ECS-normalized,
detection-enriched triage in Elasticsearch with a dedicated GUI.

Design spec: `docs/superpowers/specs/2026-07-03-raptorscope-design.md`

## Status

- **Phase 1 (core pipeline):** done — the end-to-end spine (collection →
  normalize → index → one paired detection).
- **Phase 2 (artifact breadth):** done — mappers + paired detections for the v1
  macOS artifact set (below).
- **Phase 3 (backend API):** done — FastAPI query layer (cases, overview,
  per-artifact views, timeline, alerts) over a `Store` abstraction.
- **Phase 4 (GUI):** done — React/TypeScript SPA under `web/` (case picker,
  overview, per-artifact tables, timeline, alerts with pivot-to-evidence).
- Phase 5 (packaging/docs/demo) is deferred; see `docs/superpowers/plans/`.

## v1 artifact coverage

| Artifact (Velociraptor)              | Normalizer                     | ECS dataset        | Paired detection |
|--------------------------------------|--------------------------------|--------------------|------------------|
| Launch agents/daemons                | `normalize/launch_items.py`    | `macos.persistence`| suspicious plist path |
| Login items                          | `normalize/login_items.py`     | `macos.persistence`| login item in staging dir |
| cron / periodic                      | `normalize/cron.py`            | `macos.persistence`| suspicious cron command |
| Config / MDM profiles                | `normalize/config_profiles.py` | `macos.persistence`| unsigned profile |
| Background Task Management (BTM)      | `normalize/btm.py`             | `macos.persistence`| BTM item in staging dir |
| Running processes                    | `normalize/processes.py`       | `macos.process`    | process from suspicious path |
| LSQuarantine downloads               | `normalize/quarantine.py`      | `macos.quarantine` | quarantined executable/script |
| TCC privacy grants                   | `normalize/tcc.py`             | `macos.tcc`        | sensitive grant to non-Apple client |
| Installed applications               | `normalize/inventory.py`       | `macos.inventory`  | unsigned app outside /Applications |

The persistence family shares `macos.persistence`, discriminated by
`raptorscope.persistence.type`. Every dataset is guarded against detection drift
by `detect/pairing.py` (`check_pairing(ALL_DATASETS, …)` must return `[]`).

## Usage

```bash
# dev setup
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

# run the tests
PYTHONPATH=src .venv/bin/python -m pytest tests/ -v

# ingest a Velociraptor collection (directory or zip) — dry run prints a doc count
PYTHONPATH=src .venv/bin/python -m raptorscope ingest <collection-dir>

# ...and index into Elasticsearch
PYTHONPATH=src .venv/bin/python -m raptorscope ingest <collection-dir> --es http://localhost:9200

# serve the query API — offline over a collection (demo) or over a live ES
PYTHONPATH=src .venv/bin/python -m raptorscope serve --collection <collection-dir> --port 8000
PYTHONPATH=src .venv/bin/python -m raptorscope serve --es http://localhost:9200
```

### Query API

`create_app(store)` (`api/app.py`) serves JSON over a `Store` abstraction —
`InMemoryStore` for tests/offline demo, `ESStore` for a live Elasticsearch. A
*case* is a collected host. Alerts are query-on-read: the Sigma YAMLs are
evaluated in-process (`detect/evaluate.py`) against the case's docs.

| Endpoint | Returns |
|----------|---------|
| `GET /health` | liveness |
| `GET /cases`, `GET /cases/{case}` | cases with doc counts + datasets |
| `GET /cases/{case}/overview` | first-hour counts, persistence-type + signed/unsigned breakdown |
| `GET /cases/{case}/artifacts/{dataset}` | paginated docs (`?limit=&offset=`) |
| `GET /cases/{case}/timeline` | events across datasets, newest first |
| `GET /cases/{case}/alerts` | fired detections with `doc_id` pivot-to-evidence |

### GUI (`web/`)

A Vite + React + TypeScript SPA that consumes the query API. It talks only to a
typed `ApiClient` provided via context, so every component/interaction test runs
on an in-memory fake client — no network. The app: pick a case → tabbed workspace
(Overview / Artifacts / Timeline / Alerts); clicking an alert pivots into the
Artifacts tab for that dataset with the evidence row highlighted.

```bash
cd web
npm install
npm run dev        # Vite dev server; proxies /api -> http://127.0.0.1:8000
npm test           # Vitest component + interaction tests
npm run build      # tsc typecheck + production bundle

# in another terminal, serve the API the SPA calls:
PYTHONPATH=../src ../.venv/bin/python -m raptorscope serve --collection <dir> --port 8000
```

A collection is a directory (or zip) of `<artifact>.json` files (one per artifact,
named by the stems in `cli._NORMALIZERS`) plus an optional `host.json` for
`host.*`/`user.*` context. Docs are routed to per-dataset `raptorscope-*` indices.

License: GPL-3.0-or-later
