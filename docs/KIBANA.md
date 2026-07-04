# Using Kibana with Raptorscope

Raptorscope ships its own purpose-built triage GUI (`web/`), but because it
normalizes to **ECS** and indexes into Elasticsearch, you can also explore the
same data in **Kibana** — useful for ad-hoc pivots, custom visualizations, and
teams that already live in Kibana. The two are complementary: the SPA for guided
first-hour triage and paired detections; Kibana for open-ended analysis.

## 1. Bring up Elasticsearch + Kibana

```bash
docker compose up -d          # ES on :9200, Kibana on :5601 (security off, dev only)
```

## 2. Ingest into Elasticsearch

```bash
raptorscope ingest samples/mac-victim --es http://localhost:9200
# or a real collection:
raptorscope ingest Collection-<host>.zip --es http://localhost:9200
```

Docs land in per-dataset `raptorscope-*` indices with ECS field types from the
shipped index template.

## 3. Provision the data view

```bash
./kibana/provision.sh          # KIBANA=http://localhost:5601 by default
```

This imports `kibana/saved_objects.ndjson` — a **`raptorscope-*` data view**
(time field `@timestamp`) and a **"Raptorscope — all events"** saved search — or,
if import is unavailable, creates the data view directly via the Kibana API.

## 4. Explore

Open <http://localhost:5601/app/discover> and select the **Raptorscope** data
view. Useful starting points:

- Filter by host: `host.name : "mac-victim"`
- Persistence only: `event.dataset : "macos.persistence"`
- Unsigned processes: `event.dataset : "macos.process" and not process.code_signature.trusted : true`
- Suspicious paths: `file.path : *\/tmp\/* or process.executable : *\/tmp\/*`

Build tables/pies over `event.dataset`, `raptorscope.persistence.type`,
`raptorscope.tcc.service`, etc., and assemble a dashboard.

## 5. Link from the SPA (optional)

Set `VITE_KIBANA_URL` when running the web app to surface an **“Open in Kibana ↗”**
link in the header that deep-links Discover to the current case's host:

```bash
cd web && VITE_KIBANA_URL=http://localhost:5601 npm run dev
```

> Detections remain Sigma-sourced and are evaluated by Raptorscope's own engine
> (surfaced in the SPA's Alerts tab). Kibana here is for exploration of the
> normalized events, not for running the paired detections.
