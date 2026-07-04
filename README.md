# Raptorscope

macOS DFIR analytics stack: Velociraptor macOS collections → ECS-normalized,
detection-enriched triage in Elasticsearch with a dedicated GUI.

Design spec: `docs/superpowers/specs/2026-07-03-raptorscope-design.md`

## Status

- **Phase 1 (core pipeline):** done — the end-to-end spine (collection →
  normalize → index → one paired detection).
- **Phase 2 (artifact breadth):** done — mappers + paired detections for the v1
  macOS artifact set (below).
- Phases 3–5 (backend API, GUI, packaging) are deferred; see
  `docs/superpowers/plans/`.

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
```

A collection is a directory (or zip) of `<artifact>.json` files (one per artifact,
named by the stems in `cli._NORMALIZERS`) plus an optional `host.json` for
`host.*`/`user.*` context. Docs are routed to per-dataset `raptorscope-*` indices.

License: GPL-3.0-or-later
