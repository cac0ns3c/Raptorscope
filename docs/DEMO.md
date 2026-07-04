# Raptorscope demo walkthrough

A five-minute tour of the whole stack on the bundled sample case
(`samples/mac-victim/`) — no Elasticsearch, no real collection required.

## 1. Start the stack

```bash
make setup            # first time only
make demo             # backend API on :8000, serving the sample case
```

In a second shell:

```bash
make web              # SPA dev server on http://localhost:5173
```

Open **http://localhost:5173**.

## 2. Triage the sample case

1. **Pick the case** — click `mac-victim` (22 documents across 5 datasets).
2. **Overview** — the first-hour summary: 12 persistence items, 3 processes,
   quarantine/TCC/inventory counts, and how many are unsigned.
3. **Alerts** — 11 detections fire. Click
   *“macOS persistence program in suspicious path.”*
4. **Pivot to evidence** — you land on the **Artifacts** tab, `macos.persistence`
   dataset, with the offending row (`/Users/Shared/.cache/com.system.helper.plist`)
   highlighted.
5. **Timeline** — every normalized event, newest first, across all datasets.
6. Compare with a benign case: `raptorscope serve --collection <benign-dir>` —
   the Alerts tab shows an all-clear state.

## 3. What just happened

```
samples/mac-victim/*.json  (Velociraptor artifact output)
      │  raptorscope.collection  (artifact-name aliases → normalizers)
      ▼
  ECS documents  (normalize/*.py, pure + fixture-tested)
      │
      ▼
  in-memory Store  ──►  FastAPI query API  ──►  React SPA
                          ▲
            detect/evaluate.py runs the Sigma YAMLs (source of truth)
            over the case docs → alerts (query-on-read)
```

## 4. Using a real collection

1. Build a collector or run a hunt from `profile/raptorscope-macos.yaml`
   (see `profile/README.md`); collect on a macOS host → `Collection-<host>.zip`.
2. Point the demo/serve at it:
   ```bash
   raptorscope serve --collection Collection-<host>.zip --port 8000
   ```
   or index into Elasticsearch and serve from there:
   ```bash
   docker compose up -d
   raptorscope ingest Collection-<host>.zip --es http://localhost:9200
   raptorscope serve --es http://localhost:9200
   ```
3. Reload the SPA — the real host appears as a case.
