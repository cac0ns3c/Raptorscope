# Installing Raptorscope

Raptorscope has two parts: a **Python core + query API** and a **React SPA**. The
offline demo needs only Python; the live-Elasticsearch path and the GUI dev
server add Node and (optionally) Docker.

## Prerequisites

- **Python 3.10+** (tested on 3.10–3.14)
- **Node 18+** and npm — only for the GUI (`web/`)
- **Docker** — only for the optional live Elasticsearch (`docker-compose.yml`)

## One-shot setup

```bash
make setup      # venv + Python deps + editable install + web npm install
make test       # Python (pytest) + web (tsc + vitest) suites
```

`make setup` is equivalent to:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/pip install -e .          # exposes the `raptorscope` console script
cd web && npm install
```

## Verify

```bash
.venv/bin/raptorscope --help        # console script on PATH
make test                           # all suites green
```

## Running

- **Offline demo (no ES, no Node needed):**
  ```bash
  make demo                         # serves the bundled sample case on :8000
  ```
- **GUI dev server** (in another shell; proxies `/api` → `:8000`):
  ```bash
  make web                          # http://localhost:5173
  ```
- **Ingest a real collection:**
  ```bash
  raptorscope ingest Collection-<host>.zip           # dry-run doc count
  raptorscope ingest Collection-<host>.zip --es http://localhost:9200
  ```

## Optional: live Elasticsearch

```bash
docker compose up -d                # single-node ES on :9200 (security off, dev only)
raptorscope ingest samples/mac-victim --es http://localhost:9200
raptorscope serve  --es http://localhost:9200
```

See `docs/DEMO.md` for the end-to-end walkthrough and `profile/README.md` for
building a collector.
