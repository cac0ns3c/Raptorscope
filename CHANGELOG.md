# Changelog

All notable changes to Raptorscope. Format loosely follows
[Keep a Changelog](https://keepachangelog.com/); versions are semver.

## [0.2.0] — 2026-07-04

### Real-world fidelity
- Ingest the genuine **`MacOS.Detection.Autoruns`** artifact (per-source rows,
  nested `LaunchdConfig`/`LoginItemConfig`, `Hash`) — replaces the invented
  per-type persistence artifacts.
- Custom VQL artifacts for config profiles + BTM (no standard built-ins), and
  tolerant mappers accepting the real column names.
- **Timestamp provenance** (`raptorscope.time.source`): file-`mtime`-derived
  timestamps are badged in the timeline and caveated in AI output.
- `raptorscope detect` — per-rule fire-count report for false-positive tuning.

### Scale (Elasticsearch)
- Overview computed via ES **aggregations** (no full-case scan).
- **ES-side pagination** for artifact views.
- **ES-native detection** (`ESDetector`) runs the Sigma rules as Lucene queries
  (query-on-read); `process.command_line` remapped to `wildcard` for exact
  substring parity with the in-process evaluator (0/15 rules diverge).
- **Cross-host IOC hunt** (`/hunt`) correlating an indicator across the fleet.

### AI (Claude)
- Alert triage, case summary (timestamped incident narrative), NL→query,
  agentic copilot, and **structured IOC extraction** — each behind an injectable
  seam and configurable to any Anthropic-compatible endpoint.
- Prompt-injection hardening (untrusted-evidence fencing + guard directive),
  per-endpoint rate limits, and provider-error masking.

### Security & ops
- **RBAC** roles (viewer/analyst/admin) in the signed token; AI + hunt require
  analyst+. Append-only **audit log**, `X-Request-ID` correlation, Prometheus
  **`/metrics`**.

### Quality
- Property/fuzz tests for the Sigma evaluator (fixed an `IndexError` on
  malformed conditions). Live-Elasticsearch **integration CI** job.

## [0.1.0] — 2026-07 (initial)
- Velociraptor collection → ECS normalizers → Elasticsearch + in-memory store.
- Paired Sigma detections + in-process evaluator + pairing guard.
- FastAPI query API + React/TypeScript SPA (overview, artifacts, timeline,
  alerts, search, docs), optional bearer auth, Kibana data view + dashboard,
  Docker full stack, CI.
