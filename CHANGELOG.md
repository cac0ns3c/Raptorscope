# Changelog

All notable changes to Raptorscope. Format loosely follows
[Keep a Changelog](https://keepachangelog.com/); versions are semver.

## [Unreleased]

### Real-world fidelity — first live-capture validation
- Ran the full pipeline against a **real** macOS host (Velociraptor v0.77.1) — the
  validation blocked all along. Fixed three bugs only real data exposed:
  `normalize_inventory` crashing on a list-valued `SignedBy` (cert chain), empty
  `@timestamp` from Pslist's real `CreateTime` column, and the Netstat artifact's
  integer `Family`/`Type` + missing process name (fixed via `FamilyString`/
  `TypeString` + a Pslist join, re-verified with `velociraptor artifacts verify`).
- Drove the clean-host **false-positive count 14 → 3** by tightening the
  unsigned-app rule (exclude `/Library/` trees) and the suspicious-path rule (drop
  the noisy `command_line` `/tmp/` branch). Regression tests lock the real column
  shapes; no personal capture data is committed. See
  `docs/real-capture-validation-2026-07-05.md`.

## [0.3.0] — 2026-07-05

### New dataset — `macos.network`
- Sixth ECS dataset: host TCP/UDP connections (netstat, custom VQL) with the
  owning process — listeners + established, `source`/`destination`/`network.*` +
  `raptorscope.network.state`, direction derivation, collection-time provenance.
- Reverse/bind-shell detections (a shell/nc/socat `LISTEN` or egress connection).
- The cross-host IOC hunt now correlates on `destination.address`, so an indicator
  lights up across quarantine **and** live connections.

### Detections (15 → 38 rules)
- Rule set authored + **adversarially false-positive-hunted** by multi-agent
  workflows; candidates that fired on everyday dev activity (Nix, Homebrew,
  Puppeteer, Sparkle, dev Developer-Tools grants) were dropped, and salvaged rules
  ship a test asserting the exact FP scenario stays silent.
- Fixed two rules that were **dead on real captures** — quarantine keyed on a
  filename real `QuarantineEventsV2` never emits (now matches the download URL),
  and the untrusted-process rule (now `code_signature.trusted:false`).
- **Signature-enrichment custom VQL** (`SignedProcesses`, `SignedAutoruns`) so
  `trusted:false` process/persistence rules fire on real hosts, not just fixtures.
- New coverage: the execution/LOLBin surface (osascript, spctl/csrutil, xattr,
  inline interpreters, base64→shell, launchctl-from-staging-path), sensitive TCC
  grants, ingress (tunneling/anon-drop/URL-shortener/chat-CDN hosts), keychain
  dump, dscl account creation, sqlite3 TCC tamper, inventory adware/unsigned apps.
- **MITRE hygiene**: sub-technique-precise tags across all rules; corrected a
  Windows-only technique tag misapplied to a macOS rule.

### Hardening (code-review pass)
- Rate-limited **429s are now audited, logged, and metered** (they were returning
  before the observability middleware — the throttled abuse paths were invisible).
- **Store equivalence**: `InMemoryStore` and `ESStore` now agree on `page()` and
  `search()` ordering (deterministic `@timestamp` default sort + stable tiebreak);
  `hunt()` escapes wildcard metacharacters so an IOC matches as a literal substring.
- **Web**: a mid-session **401 routes back to login** (any call, not just the
  mount-time probe); fleet-hunt and NL-query failures surface instead of silently
  idling.
- Correct Sigma **quantifier conditions** (`N of` / `all of` / prefix) in the
  in-process evaluator, closing a latent parity gap vs pysigma/ES.
- **Supply chain**: bounded `requirements.txt` majors (`pysigma<2`, …) to bracket
  the CVE-audited `requirements.lock`, so a fresh resolve can't pull a breaking
  major into the detection engine.

### Tooling & docs
- Project **subagents** — `code-reviewer`, `detection-engineer`, `pm`,
  `security-engineer` — tailored to the repo's invariants (`.claude/agents/`).
- Showcase README (architecture diagram + engineering highlights), plus
  **CI-captured SPA screenshots and a guided-tour GIF** that regenerate each run.

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
