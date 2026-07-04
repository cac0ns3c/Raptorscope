# Raptorscope Backend API (Phase 3) Implementation Plan

**Goal:** Ship the FastAPI query layer the SPA depends on — cases, first-hour
overview, per-artifact views, unified timeline, and detection alerts with
pivot-to-evidence — over a **storage abstraction** so every endpoint is
contract-tested against an in-memory store seeded from the Phase-2 fixtures, with
no live Elasticsearch required.

**Spec reference:** design spec §4 (component 5, GUI backend API) and §5b (GUI
scope items 1–5). This is phasing step 3.

**Architecture:** A `Store` protocol (`api/store.py`) abstracts the datastore:
`InMemoryStore` for tests/dev, `ESStore` wrapping the elasticsearch client for
prod — both return the same ECS docs Phase 2 produces. `create_app(store)`
(`api/app.py`) builds a FastAPI app with the store injected via FastAPI
dependency override, so tests swap in a seeded `InMemoryStore`. A **case** is a
collected host (`host.name`). Alerts are **query-on-read**: Sigma YAMLs (still the
source of truth) are evaluated in-process by a small, bounded matcher
(`detect/evaluate.py`) against the case's docs — the same rules the Lucene
converter and pairing guard already use.

**Tech stack:** adds `fastapi`, `uvicorn`, `httpx` (TestClient). Everything else
unchanged.

## Global Constraints

- Same as Phases 1–2: SPDX header on every source file; GPL-3.0-or-later; DCO
  sign-off; ECS/`raptorscope.*` schema; Sigma is the detection source of truth;
  unit/contract tests take **no live infra** (in-memory store only). `ESStore` is
  a thin prod adapter, exercised only behind a skipped integration test.
- New runtime deps (`fastapi`, `uvicorn`) go in **both** `pyproject.toml` and
  `requirements.txt`; `httpx` is a test dep.

## Endpoints (all JSON)

| Method/path | Returns |
|-------------|---------|
| `GET /health` | `{"status":"ok"}` |
| `GET /cases` | list of cases: `{name, doc_count, datasets}` |
| `GET /cases/{case}` | one case summary (404 if unknown) |
| `GET /cases/{case}/overview` | per-dataset counts, persistence-type breakdown, signed/unsigned tallies |
| `GET /cases/{case}/artifacts/{dataset}` | paginated docs for a dataset (`?limit=&offset=`) |
| `GET /cases/{case}/timeline` | events across datasets sorted by `@timestamp` (compact projection) |
| `GET /cases/{case}/alerts` | fired detections with `{rule_id,title,level,dataset,doc_id,evidence}` |

---

### Task 1: Store abstraction + app scaffold + `/health`

- `api/__init__.py`, `api/store.py` (`Store` Protocol: `hosts()`, `datasets()`,
  `count(host,dataset)`, `search(host,dataset,size,sort)`, `get(doc_id)`;
  `InMemoryStore(docs)` assigns a stable `_id` per doc), `api/app.py`
  (`create_app(store) -> FastAPI`, `/health`, store via `Depends`).
- `tests/api/conftest.py`: `seed_store()` builds an `InMemoryStore` from all
  Phase-2 fixtures via the normalizers (two hosts so multi-case is exercised).
- Tests: `/health` ok; `InMemoryStore` search filters by host+dataset.

### Task 2: Cases — `GET /cases`, `GET /cases/{case}`

- Derive cases from distinct `host.name`. `/cases` → list with doc_count +
  datasets present; `/cases/{case}` → same for one host, 404 otherwise.
- Tests: both hosts listed; counts correct; unknown case → 404.

### Task 3: Overview — `GET /cases/{case}/overview`

- Aggregate for the case: `datasets` (dataset→count),
  `persistence_types` (type→count), `unsigned` counts for process/inventory,
  `total`.
- Tests: dataset counts match seed; persistence-type breakdown includes
  launch/login/cron/config_profile/btm; unknown case → 404.

### Task 4: Per-artifact views — `GET /cases/{case}/artifacts/{dataset}`

- Return `{total, items}` for `host+dataset` with `?limit`(default 50)/`?offset`.
- Tests: dataset filter works; pagination slices; bad dataset → empty/`total:0`;
  unknown case → 404.

### Task 5: Timeline — `GET /cases/{case}/timeline`

- Merge all case docs, sort by `@timestamp` desc, project
  `{timestamp,dataset,category,summary,doc_id}` where `summary` is a per-dataset
  one-liner. `?limit` default 100.
- Tests: sorted desc; mixes datasets; each row has a doc_id resolvable via
  `store.get`.

### Task 6: Detection evaluator — `detect/evaluate.py` (pure)

- `load_rules(rules_dir) -> list[Rule]` (id,title,level,tags,datasets,detection).
- `rule_matches(doc, detection) -> bool`: field lookup by dotted path; modifiers
  `contains`/`startswith`/`endswith`; list value = OR; multiple fields in a block
  = AND; a tiny boolean evaluator over named selection blocks for `condition`
  (`and`/`or`/`not`/parens) — covering `selection` and `selection and not filter`.
- `run_rules(docs, rules) -> list[alert]`.
- Tests (no API): each Phase-1/2 rule fires on its intended fixture row and stays
  quiet on benign rows; the `condition … not filter` rules (TCC, inventory)
  respect the exclusion.

### Task 7: Alerts endpoint + prod adapter + `serve` CLI

- `GET /cases/{case}/alerts` runs `detect/evaluate` over the case's docs and
  returns fired alerts with pivot (`dataset`,`doc_id`, `evidence` = the matched
  fields), sorted by level then dataset.
- `es/store.py` `ESStore` implementing `Store` over the elasticsearch client
  (search/count/get across `raptorscope-*`); behind a skipped integration test.
- CLI `raptorscope serve [--es URL] [--host --port]`: builds `create_app` with
  `ESStore` (or a store loaded from a collection dir for offline demo) and runs
  uvicorn.
- Tests: alerts fire for the seeded case; each alert's `doc_id` resolves and its
  `dataset` matches; benign-only case yields no alerts; unknown case → 404.

## Self-review notes

- **Spec coverage:** endpoints map 1:1 to GUI scope §5b (case select, overview,
  per-artifact, timeline, alerts+pivot). Backend queries the store; Sigma stays
  source of truth via in-process evaluation of the same YAMLs.
- **No live infra:** the `Store` seam keeps all contract tests in-memory; ES is a
  prod-only adapter. Matches spec §6 testing strategy.
- **UI-agnostic core intact:** the SPA (Phase 4) will consume these stable JSON
  contracts; nothing here depends on the frontend.
