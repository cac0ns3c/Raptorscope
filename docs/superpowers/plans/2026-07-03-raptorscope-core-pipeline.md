# Raptorscope Core Pipeline (Phase 1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up the end-to-end spine — a Velociraptor macOS collection (persistence artifact) is normalized to ECS, indexed into Elasticsearch, and one paired Sigma detection fires — proving every downstream layer before breadth is added.

**Architecture:** A pure-Python core: `normalize/` maps captured Velociraptor rows → ECS docs (no I/O, fixture-tested); `es/` ships an index template + a thin bulk indexer; `detect/` holds Sigma sources, a Sigma→Elastic converter, and a pairing guard; `cli.py` wires zip → normalize → index. The vertical slice is one artifact (LaunchAgents/LaunchDaemons persistence) so every layer is exercised once.

**Tech Stack:** Python 3.10+, `elasticsearch` client, `pysigma` + `pysigma-backend-elasticsearch` (`sigma-cli`), `pytest`. Elasticsearch 8.x as backend (OpenSearch is a later drop-in). No frontend in this phase.

## Global Constraints

- Python 3.10+; code must pass on 3.10–3.12.
- Every source file starts with `# SPDX-License-Identifier: GPL-3.0-or-later`.
- License GPL-3.0-or-later; commits signed off (`git commit -s`, DCO).
- New runtime deps go in **both** `pyproject.toml` and `requirements.txt`.
- Target schema is **Elastic Common Schema (ECS)**; macOS-specific fields with no ECS home go under a namespaced `raptorscope.*`.
- Sigma YAMLs under `detections/sigma/` are the detection **source of truth**; Elastic queries are generated, never hand-written.
- Unit tests take **no live infra** — normalizer and detection tests are pure; ES integration tests are separate and skip when no ES is reachable.

---

### Task 1: Project scaffold

**Files:**
- Create: `pyproject.toml`, `requirements.txt`, `.gitignore`, `src/raptorscope/__init__.py`, `tests/__init__.py`, `tests/test_smoke.py`
- Create: `src/raptorscope/normalize/__init__.py`, `src/raptorscope/es/__init__.py`, `src/raptorscope/detect/__init__.py`

**Interfaces:**
- Produces: an importable `raptorscope` package; `PYTHONPATH=src pytest` runs green.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_smoke.py
# SPDX-License-Identifier: GPL-3.0-or-later
import raptorscope

def test_package_has_version():
    assert isinstance(raptorscope.__version__, str)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src python -m pytest tests/test_smoke.py -v`
Expected: FAIL (`ModuleNotFoundError: raptorscope` or missing `__version__`).

- [ ] **Step 3: Create the package + config**

`src/raptorscope/__init__.py`:
```python
# SPDX-License-Identifier: GPL-3.0-or-later
__version__ = "0.0.1"
```
Create empty SPDX-headed `__init__.py` in `normalize/`, `es/`, `detect/`, and `tests/`.
`pyproject.toml`: project name `raptorscope`, version `0.0.1`, `requires-python = ">=3.10"`, license `GPL-3.0-or-later`, deps `elasticsearch>=8.11`, `pysigma>=0.11`, `pysigma-backend-elasticsearch>=1.1`; `[tool.pytest.ini_options] pythonpath = ["src"]`.
`requirements.txt`: the same three runtime deps + `pytest`.
`.gitignore`: `__pycache__/`, `*.pyc`, `.venv/`, `build/`, `dist/`, `*.egg-info/`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `PYTHONPATH=src python -m pytest tests/ -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -s -m "chore: scaffold raptorscope package"
```

---

### Task 2: Velociraptor macOS persistence spike → real fixture

**Files:**
- Create: `fixtures/velociraptor/launch_items.raw.json` (captured real output)
- Create: `docs/spikes/2026-07-03-velociraptor-macos-persistence.md` (findings)

**Interfaces:**
- Produces: `fixtures/velociraptor/launch_items.raw.json` — a JSON array of the actual rows Velociraptor emits for the LaunchAgents/LaunchDaemons persistence artifact, plus the exact artifact name and column names. Task 3's test is written against this file.

> This is a spike, not TDD. Its deliverable is a real fixture + a findings note. Do not proceed to Task 3 until the fixture reflects genuine Velociraptor output.

- [ ] **Step 1: Identify the artifact**

Run `velociraptor artifacts list | grep -i -E 'launch|persist|autoruns|plist'` (or browse the artifact reference). Record the exact artifact name (e.g. `MacOS.System.LaunchServices` / `MacOS.Autoruns` / a `Plist`-based one). Note its declared columns.

- [ ] **Step 2: Collect on a macOS host**

Build a minimal offline collector for just that artifact and run it on a Mac (or this host):
```bash
velociraptor artifacts collect <ArtifactName> --format json > fixtures/velociraptor/launch_items.raw.json
```
If no live Mac is available, hand-author the fixture from the artifact's documented column schema and mark it `SYNTHETIC` in the findings note — Task 3 tests still bind to these field names.

- [ ] **Step 3: Trim + record**

Keep 3–6 representative rows (at least one LaunchAgent and one LaunchDaemon; include one with `ProgramArguments`, one with a `Program`, and if possible one unsigned/quarantined). In the findings note, write: exact artifact name, every column name used downstream, and any surprises (nested plists, list-vs-string `Program`).

- [ ] **Step 4: Commit**

```bash
git add fixtures/ docs/spikes/ && git commit -s -m "spike: capture Velociraptor macOS persistence output as fixture"
```

---

### Task 3: ECS normalizer for the persistence artifact

**Files:**
- Create: `src/raptorscope/normalize/launch_items.py`
- Create: `src/raptorscope/normalize/ecs.py` (shared ECS helpers)
- Test: `tests/normalize/test_launch_items.py`

**Interfaces:**
- Consumes: `fixtures/velociraptor/launch_items.raw.json` from Task 2.
- Produces:
  - `normalize_launch_items(rows: list[dict], host: dict) -> list[dict]` in `launch_items.py`. Each output doc is ECS-shaped:
    - `@timestamp` (ISO8601 str), `event.kind="event"`, `event.category=["configuration"]`, `event.type=["info"]`, `event.module="raptorscope"`, `event.dataset="macos.persistence"`
    - `host` = the passed host dict (`host.name`, `host.os.type="macos"`)
    - `file.path`, `file.name` = the plist path
    - `process.executable` (the Program), `process.command_line` (Program + ProgramArguments joined), `process.code_signature.exists`/`.subject_name`/`.trusted` when present
    - `raptorscope.persistence.type` = `"launch_agent"` if path under a `LaunchAgents` dir else `"launch_daemon"`, `raptorscope.persistence.label`, `raptorscope.persistence.run_at_load` (bool)
  - `ecs_base(host: dict, dataset: str) -> dict` in `ecs.py` returning the common `event.*`/`host.*` skeleton.

- [ ] **Step 1: Write the failing test** (bind assertions to the REAL fixture from Task 2)

```python
# tests/normalize/test_launch_items.py
# SPDX-License-Identifier: GPL-3.0-or-later
import json, pathlib
from raptorscope.normalize.launch_items import normalize_launch_items

ROWS = json.loads((pathlib.Path("fixtures/velociraptor/launch_items.raw.json")).read_text())
HOST = {"name": "mac-victim", "os": {"type": "macos"}}

def test_maps_each_row_to_one_ecs_doc():
    docs = normalize_launch_items(ROWS, HOST)
    assert len(docs) == len(ROWS)

def test_persistence_type_from_path():
    docs = normalize_launch_items(ROWS, HOST)
    types = {d["raptorscope"]["persistence"]["type"] for d in docs}
    assert types <= {"launch_agent", "launch_daemon"}
    for d in docs:
        assert d["event"]["dataset"] == "macos.persistence"
        assert d["host"]["os"]["type"] == "macos"
        assert d["file"]["path"]  # plist path present

def test_program_becomes_process_executable():
    docs = normalize_launch_items(ROWS, HOST)
    assert any(d.get("process", {}).get("executable") for d in docs)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src python -m pytest tests/normalize/test_launch_items.py -v`
Expected: FAIL (`ModuleNotFoundError`).

- [ ] **Step 3: Implement `ecs.py` then `launch_items.py`**

```python
# src/raptorscope/normalize/ecs.py
# SPDX-License-Identifier: GPL-3.0-or-later
def ecs_base(host: dict, dataset: str) -> dict:
    return {
        "event": {"kind": "event", "module": "raptorscope",
                  "dataset": dataset, "category": ["configuration"], "type": ["info"]},
        "host": host,
    }
```
```python
# src/raptorscope/normalize/launch_items.py
# SPDX-License-Identifier: GPL-3.0-or-later
import os
from .ecs import ecs_base

def _persistence_type(path: str) -> str:
    return "launch_agent" if "LaunchAgents" in (path or "") else "launch_daemon"

def normalize_launch_items(rows: list[dict], host: dict) -> list[dict]:
    docs = []
    for r in rows:
        # Field names below are CONFIRMED against fixtures/velociraptor/launch_items.raw.json (Task 2).
        path = r.get("Path") or r.get("_Source") or ""
        program = r.get("Program")
        args = r.get("ProgramArguments") or []
        if isinstance(args, str):
            args = [args]
        executable = program or (args[0] if args else None)
        cmdline = " ".join([program, *args]) if program else " ".join(args)
        doc = ecs_base(host, "macos.persistence")
        doc["@timestamp"] = r.get("Mtime") or r.get("_ts") or ""
        doc["file"] = {"path": path, "name": os.path.basename(path)}
        if executable:
            doc["process"] = {"executable": executable, "command_line": cmdline or executable}
        doc["raptorscope"] = {"persistence": {
            "type": _persistence_type(path),
            "label": r.get("Label"),
            "run_at_load": bool(r.get("RunAtLoad")),
        }}
        docs.append(doc)
    return docs
```
Adjust the `r.get(...)` source keys to the EXACT column names recorded in Task 2's findings note.

- [ ] **Step 4: Run tests to verify they pass**

Run: `PYTHONPATH=src python -m pytest tests/normalize/ -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -s -m "feat(normalize): ECS mapper for macOS launch-item persistence"
```

---

### Task 4: Elasticsearch index template + bulk indexer

**Files:**
- Create: `src/raptorscope/es/template.py` (the component/index template dict)
- Create: `src/raptorscope/es/indexer.py` (bulk indexer wrapper)
- Test: `tests/es/test_indexer.py`

**Interfaces:**
- Consumes: ECS docs from Task 3.
- Produces:
  - `INDEX_TEMPLATE: dict` and `INDEX_PATTERN="raptorscope-*"` in `template.py`.
  - `bulk_index(client, index: str, docs: list[dict]) -> int` in `indexer.py` — returns count indexed; builds `_bulk` actions and calls `elasticsearch.helpers.bulk`.

- [ ] **Step 1: Write the failing test** (mock the ES client — no live infra)

```python
# tests/es/test_indexer.py
# SPDX-License-Identifier: GPL-3.0-or-later
from unittest.mock import patch
from raptorscope.es.indexer import bulk_index
from raptorscope.es.template import INDEX_TEMPLATE, INDEX_PATTERN

def test_template_targets_pattern():
    assert INDEX_PATTERN == "raptorscope-*"
    assert "template" in INDEX_TEMPLATE

def test_bulk_index_sends_all_docs():
    docs = [{"@timestamp": "t", "event": {"dataset": "macos.persistence"}}]
    with patch("raptorscope.es.indexer.helpers.bulk", return_value=(1, [])) as m:
        n = bulk_index(client=object(), index="raptorscope-persistence", docs=docs)
    assert n == 1
    actions = list(m.call_args.args[1])
    assert actions[0]["_index"] == "raptorscope-persistence"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src python -m pytest tests/es/test_indexer.py -v`
Expected: FAIL (`ModuleNotFoundError`).

- [ ] **Step 3: Implement template + indexer**

```python
# src/raptorscope/es/template.py
# SPDX-License-Identifier: GPL-3.0-or-later
INDEX_PATTERN = "raptorscope-*"
INDEX_TEMPLATE = {
    "index_patterns": [INDEX_PATTERN],
    "template": {"mappings": {"dynamic": True, "properties": {
        "@timestamp": {"type": "date"},
        "event": {"properties": {"dataset": {"type": "keyword"}, "category": {"type": "keyword"}}},
        "host": {"properties": {"name": {"type": "keyword"}}},
        "file": {"properties": {"path": {"type": "keyword"}, "name": {"type": "keyword"}}},
        "process": {"properties": {"executable": {"type": "keyword"}, "command_line": {"type": "text"}}},
    }}},
}
```
```python
# src/raptorscope/es/indexer.py
# SPDX-License-Identifier: GPL-3.0-or-later
from elasticsearch import helpers

def bulk_index(client, index: str, docs: list[dict]) -> int:
    actions = ({"_index": index, "_source": d} for d in docs)
    ok, _ = helpers.bulk(client, actions)
    return ok
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `PYTHONPATH=src python -m pytest tests/es/ -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -s -m "feat(es): index template + bulk indexer"
```

---

### Task 5: First paired Sigma detection + converter + pairing guard

**Files:**
- Create: `detections/sigma/macos_persistence_suspicious_path.yml`
- Create: `src/raptorscope/detect/convert.py` (Sigma→Elastic)
- Create: `src/raptorscope/detect/pairing.py` (guard: dataset↔rule coverage + dead-field check)
- Test: `tests/detect/test_sigma_rules.py`, `tests/detect/test_pairing.py`

**Interfaces:**
- Consumes: normalized field names from Task 3; `detections/sigma/*.yml`.
- Produces:
  - `convert_rule(path: str) -> str` in `convert.py` — returns the Elastic (Lucene) query string for a Sigma file via pysigma's elasticsearch backend.
  - `check_pairing(datasets: set[str], rules_dir: str) -> list[str]` in `pairing.py` — returns a list of problems (empty = OK): a dataset with no rule, or a rule selecting a field the normalizer never emits.

- [ ] **Step 1: Write the failing tests**

```python
# tests/detect/test_sigma_rules.py
# SPDX-License-Identifier: GPL-3.0-or-later
from raptorscope.detect.convert import convert_rule

def test_rule_converts_to_elastic_query():
    q = convert_rule("detections/sigma/macos_persistence_suspicious_path.yml")
    assert "file.path" in q  # selects on the normalized ECS field
```
```python
# tests/detect/test_pairing.py
# SPDX-License-Identifier: GPL-3.0-or-later
from raptorscope.detect.pairing import check_pairing

def test_persistence_dataset_is_paired():
    problems = check_pairing({"macos.persistence"}, "detections/sigma")
    assert problems == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `PYTHONPATH=src python -m pytest tests/detect/ -v`
Expected: FAIL (module + rule file missing).

- [ ] **Step 3: Author the Sigma rule + implement convert/pairing**

`detections/sigma/macos_persistence_suspicious_path.yml`:
```yaml
title: macOS persistence program in suspicious path
id: 5a1e0b7c-0000-4000-a000-raptorscope01
status: experimental
logsource: {product: macos, service: persistence}
detection:
  selection:
    event.dataset: macos.persistence
    file.path|contains:
      - /tmp/
      - /private/tmp/
      - /Users/Shared/
  condition: selection
level: high
tags: [attack.persistence, attack.t1543]
```
```python
# src/raptorscope/detect/convert.py
# SPDX-License-Identifier: GPL-3.0-or-later
from pathlib import Path
from sigma.collection import SigmaCollection
from sigma.backends.elasticsearch import LuceneBackend

def convert_rule(path: str) -> str:
    col = SigmaCollection.from_yaml(Path(path).read_text())
    return LuceneBackend().convert(col)[0]
```
```python
# src/raptorscope/detect/pairing.py
# SPDX-License-Identifier: GPL-3.0-or-later
import glob, yaml

# Fields the normalizers are known to emit (extend as datasets are added).
EMITTED_FIELDS = {"event.dataset", "file.path", "file.name",
                  "process.executable", "process.command_line",
                  "raptorscope.persistence.type", "raptorscope.persistence.label"}

def _rule_datasets_and_fields(doc):
    det = doc.get("detection", {})
    datasets, fields = set(), set()
    for key, sel in det.items():
        if not isinstance(sel, dict):
            continue
        for field, val in sel.items():
            base = field.split("|")[0]
            fields.add(base)
            if base == "event.dataset":
                datasets.update(v for v in ([val] if isinstance(val, str) else val))
    return datasets, fields

def check_pairing(datasets: set, rules_dir: str) -> list:
    problems, covered = [], set()
    for path in glob.glob(f"{rules_dir}/*.yml"):
        doc = yaml.safe_load(open(path))
        ds, fields = _rule_datasets_and_fields(doc)
        covered |= ds
        dead = {f for f in fields if f not in EMITTED_FIELDS}
        if dead:
            problems.append(f"{path}: selects unknown fields {sorted(dead)}")
    for d in datasets - covered:
        problems.append(f"dataset '{d}' has no paired Sigma rule")
    return problems
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `PYTHONPATH=src python -m pytest tests/detect/ -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -s -m "feat(detect): first paired macOS persistence rule + converter + pairing guard"
```

---

### Task 6: CLI — ingest a collection → normalize → index

**Files:**
- Create: `src/raptorscope/collection.py` (read a Velociraptor collection zip/dir → `{artifact: rows}` + host)
- Create: `src/raptorscope/cli.py` (`python -m raptorscope ingest <path> --es <url>`)
- Test: `tests/test_collection.py`, `tests/test_cli.py`

**Interfaces:**
- Consumes: `normalize_launch_items` (Task 3), `bulk_index` (Task 4).
- Produces:
  - `load_collection(path: str) -> tuple[dict, dict]` in `collection.py` — returns `(artifacts, host)` where `artifacts` maps artifact name → list of rows.
  - `ingest(path: str, es_url: str | None) -> int` in `cli.py` — normalizes known artifacts and (if `es_url`) indexes; returns total docs. With no `es_url`, prints doc count (dry run).

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_collection.py
# SPDX-License-Identifier: GPL-3.0-or-later
import json, pathlib
from raptorscope.collection import load_collection

def test_loads_rows_and_host(tmp_path):
    d = tmp_path / "col"; d.mkdir()
    (d / "launch_items.json").write_text(json.dumps([{"Path": "/tmp/x.plist"}]))
    (d / "host.json").write_text(json.dumps({"name": "mac-1"}))
    artifacts, host = load_collection(str(d))
    assert host["name"] == "mac-1"
    assert artifacts["launch_items"][0]["Path"] == "/tmp/x.plist"
```
```python
# tests/test_cli.py
# SPDX-License-Identifier: GPL-3.0-or-later
import json
from raptorscope.cli import ingest

def test_ingest_dry_run_counts(tmp_path, capsys):
    d = tmp_path / "col"; d.mkdir()
    (d / "launch_items.json").write_text(json.dumps([{"Path": "/tmp/x.plist", "Label": "evil"}]))
    (d / "host.json").write_text(json.dumps({"name": "mac-1", "os": {"type": "macos"}}))
    n = ingest(str(d), es_url=None)
    assert n == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `PYTHONPATH=src python -m pytest tests/test_collection.py tests/test_cli.py -v`
Expected: FAIL (`ModuleNotFoundError`).

- [ ] **Step 3: Implement collection loader + CLI**

```python
# src/raptorscope/collection.py
# SPDX-License-Identifier: GPL-3.0-or-later
import json, pathlib

def load_collection(path: str) -> tuple[dict, dict]:
    root = pathlib.Path(path)
    host = json.loads((root / "host.json").read_text()) if (root / "host.json").exists() else {}
    artifacts = {}
    for f in root.glob("*.json"):
        if f.name == "host.json":
            continue
        artifacts[f.stem] = json.loads(f.read_text())
    return artifacts, host
```
```python
# src/raptorscope/cli.py
# SPDX-License-Identifier: GPL-3.0-or-later
import argparse
from .collection import load_collection
from .normalize.launch_items import normalize_launch_items

_NORMALIZERS = {"launch_items": normalize_launch_items}

def ingest(path: str, es_url: str | None) -> int:
    artifacts, host = load_collection(path)
    docs = []
    for name, fn in _NORMALIZERS.items():
        if name in artifacts:
            docs.extend(fn(artifacts[name], host))
    if es_url:
        from elasticsearch import Elasticsearch
        from .es.indexer import bulk_index
        bulk_index(Elasticsearch(es_url), "raptorscope-persistence", docs)
    print(f"{len(docs)} docs")
    return len(docs)

def main(argv=None):
    p = argparse.ArgumentParser(prog="raptorscope")
    sub = p.add_subparsers(dest="cmd", required=True)
    ing = sub.add_parser("ingest"); ing.add_argument("path"); ing.add_argument("--es", default=None)
    a = p.parse_args(argv)
    if a.cmd == "ingest":
        ingest(a.path, a.es)

if __name__ == "__main__":
    main()
```
Add `__main__.py` re-exporting `main` so `python -m raptorscope` works.

- [ ] **Step 4: Run the full suite**

Run: `PYTHONPATH=src python -m pytest tests/ -v`
Expected: PASS (all tasks green together).

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -s -m "feat(cli): ingest collection -> normalize -> index vertical slice"
```

---

## Follow-on plans (roadmap — not in this plan)

Each is its own spec→plan→build cycle, and each produces working software:

- **Phase 2 — Artifact breadth:** mappers + paired detections for the rest of the v1 set (LoginItems, cron/periodic, config profiles, BTM, processes, quarantine, TCC, inventory/host).
- **Phase 3 — Backend API:** FastAPI query endpoints the SPA needs (cases, per-artifact views, timeline, alerts).
- **Phase 4 — GUI:** React/TypeScript SPA implementing the v1 GUI scope.
- **Phase 5 — Packaging/docs/demo:** collector build UX, install docs, sample-case demo.

## Self-review notes

- **Spec coverage:** Phase 1 covers collection profile (spike, Task 2), normalizer (Task 3), ES schema (Task 4), paired detection + guard (Task 5), CLI glue (Task 6). GUI/backend/breadth are explicitly deferred to named follow-on plans — consistent with spec §9 phasing.
- **Chicken-and-egg:** normalizer field names are resolved by the Task 2 fixture; Task 3's test binds to the real fixture, so wrong guesses fail loudly.
- **Guardrail honored:** the core (Tasks 1–6) is UI-agnostic and ships value without any GUI.
