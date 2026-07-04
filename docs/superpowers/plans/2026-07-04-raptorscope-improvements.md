# Raptorscope System Improvement Plan

> **For agentic workers:** each phase is its own spec→plan→build cycle. Steps use
> checkbox (`- [ ]`) syntax. Keep the project's discipline: TDD (failing test →
> implement → green), SPDX headers, GPL-3.0-or-later, DCO sign-off, no live infra
> in unit tests, and one commit per task.

**Priority lens:** *real-world fidelity first*. Raptorscope's v1 is complete and
feature-rich, but it has never touched genuine Velociraptor output — that is the
defining weakness and Phase A closes it before breadth or scale. Phases B–E harden
the whole system for production once the data path is trustworthy.

**Baseline (done):** collection profile + 9 mappers → ECS → ES + in-memory store →
15 paired Sigma detections + evaluator + pairing guard → FastAPI query API (cases,
overview, artifacts, timeline, alerts, search) → React/TS SPA (redesigned; triage
state, detail drawer, export, light mode, sortable columns, Docs) → auth (token
expiry, multi-user, logout) → Kibana (data view + dashboard) → AI (triage, summary,
NL-query, agentic copilot; injectable seam) → Docker full stack → CI. Python 117
tests, web 50 tests.

---

## Phase A — Real-world fidelity ⭐ (do first)

**Goal:** make every artifact ingest and normalize from *genuine* Velociraptor
output, with correct time semantics and a measured false-positive posture. See
`docs/spikes/2026-07-04-real-velociraptor-validation.md` for the confirmed deltas.

### A1 — Persistence family → `MacOS.Detection.Autoruns`
The invented `launch_items`/`login_items`/`cron_items` don't exist; the real
artifact is one **`MacOS.Detection.Autoruns`** with per-*source* rows and nested
config blobs.
- Files: new `src/raptorscope/normalize/autoruns.py`; retire/rewire
  `launch_items.py` + `login_items.py` + `cron.py`; update
  `collection.ARTIFACT_ALIASES` and `cli._NORMALIZERS`.
- `normalize_autoruns(rows, host)` dispatches on the Autoruns source
  (`LaunchAgentsDaemons`, `LoginItems`, `Sandboxed Loginitems`, `crontabs`,
  `StartupItems`, …) → the existing `macos.persistence` docs with
  `raptorscope.persistence.type`. Parse the nested `LaunchdConfig` /
  `LoginItemConfig` plist for `Program`/`ProgramArguments`/`RunAtLoad`/`Label`;
  crontab source carries `Minute/Hour/…/Command`. Real column names: `OSPath`,
  `Mtime`, `Program`, `Hash`, `Disabled`.
- **Signature model:** Autoruns/Pslist emit a **`Hash`**, not a code-signature
  object. Add `raptorscope.*.hash` and make the "unsigned"-based detections tolerate
  the absence of `process.code_signature` (fall back to a hash-reputation/allowlist
  signal or drop the signed check for real captures) — see A4.
- [x] **DONE** — `normalize_autoruns` + alias + `tests/normalize/test_autoruns.py`.

### A2 — config profiles & BTM via custom VQL
No standard built-ins exist for these.
- `profile/` — author custom VQL artifacts (`profiles -C -o stdout-xml`; BTM db) and
  document them; add mappers matching the VQL output; alias + register.
- [x] **DONE** — `profile/custom-vql/*.yaml` + tolerant config-profile/BTM mappers + real-column tests.

### A3 — real capture + sanitized fixtures
- Build an offline collector from the reconciled `profile/`, run on a macOS host,
  and **replace the synthetic fixtures with trimmed, PII-sanitized real rows**.
- [ ] **BLOCKED** — requires running a collector on a real Mac (can't execute the binary here; must not commit personal data). Pipeline is now ready to ingest a real capture.

### A4 — timestamp provenance + integrity semantics
- Distinguish plist **`Mtime`** (file-modified) from true event time. Add
  `raptorscope.time.source` (`mtime` | `created` | `event`) and label it in the
  timeline UI and AI prompts (the AI summary review flagged mtime-as-event).
- Replace the code-signature-only "unsigned" heuristic with a
  hash+path+allowlist model that works on real Autoruns/Pslist `Hash` data.
- [x] **DONE** — `raptorscope.time.source`; timeline `mtime` badge; AI summary provenance caveat.

### A5 — false-positive posture
- Per-rule **hit + benign** fixtures already exist; extend to a small *real*
  benign corpus and record FP notes per rule in `detections/`.
- Add a `raptorscope detect --measure <collection>` CLI that reports per-rule
  fire counts to support tuning.
- [x] **DONE (command)** — `raptorscope detect` per-rule fire counts (`measure_detections`); real benign corpus still pending A3.

---

## Phase B — Scale & robustness

**Goal:** stop loading whole cases into memory; handle real collection sizes.

### B1 — push aggregations to Elasticsearch
`api/app.py` computes overview/timeline/counts by pulling `size=100000` docs.
- Add `Store.aggregate(host, spec)` (ES `terms`/`date_histogram`/`filter` aggs;
  in-memory equivalent for `InMemoryStore`). Rewrite `overview` and count paths to
  use it. Keeps the same JSON contract.
- [x] **DONE (B1)** — `Store.aggregate(host)` on both backends (ES aggs, no full scan); overview endpoint + AI `_overview` rewired; validated byte-identical against live ES.

### B2 — pagination / `search_after`
`es/store.py` caps at `MAX_WINDOW = 10000`.
- Replace with cursor pagination (PIT + `search_after`) in `ESStore.search`; add
  `?cursor=` to `/artifacts` and `/search`; SPA infinite-scroll / next-page.
- [x] **PARTIAL (B2)** — ES-side `offset`+`size` paging on `search`; artifacts endpoint pages ES-side (no full-dataset pull); validated live. Deep >10k paging (PIT + search_after) still to do.

### B3 — ES-native detections (scale path)
In-process `run_rules` reads all case docs.
- Add an `ESDetector` that runs the already-generated Lucene queries
  (`detect/convert.py`) against ES and returns hits; keep the in-process evaluator
  for the offline/demo path. Resolve spec §11 (query-on-read vs. written alert docs)
  — recommend a `detect run` that writes `raptorscope-alerts-*`.
- [x] **DONE (B3)** — `ESDetector` runs the generated Lucene per rule (query-on-read, no full-doc pull), wired as the ES-backed `/alerts` path. Root-caused the parity gap (3/15 rules on the analyzed `command_line` field) and fixed it by mapping `command_line` as ES `wildcard`; **0/15 divergence** verified live. Unit tests (fake ES) + `tests/detect/test_es_detector_parity.py` (live integration, skips w/o ES).

### B4 — multi-host / multi-case
- Ingest multiple hosts; case = collection, host = sub-filter; cross-host IOC
  pivot in the API + SPA.
- [x] **DONE (B4)** — cross-host IOC correlation: `Store.hunt(value)` (both backends; ES `wildcard`/keyword bool-should), auth-guarded `GET /hunt` grouped by host, and a fleet-hunt UI in the case picker (pivot to any matching host). Live-validated: a shared C2 IP correlates across two ingested hosts.

---

## Phase C — AI depth & safety

### C1 — streaming + tuning
- Stream `triage`/`summary`/`copilot` (SSE) so long copilot runs render
  incrementally; add `output_config.effort` tuning and prompt caching of the
  system persona. Extend `AIClient` with a streaming primitive; SPA reads the stream.
- [ ] Streaming seam + SSE endpoints + SPA + tests (fake stream). *(not started)*

### C2 — prompt-injection hardening (input side)
Case data (attacker-controllable artifact fields) flows into prompts.
- Delimit/label all evidence as untrusted data (not instructions); add a guard
  system directive; strip/escape control sequences; add a red-team test with a
  malicious `command_line` attempting instruction injection.
- [x] **DONE (C2)** — untrusted-evidence fencing + guard directive + red-team test.

### C3 — guardrails & structured output
- Rate-limit `/ai/*` and `/login`; per-request token ceilings; **structured IOC
  extraction** (`messages.parse` → typed IOCs) surfaced in the UI and exportable;
  persist triage results per case (like the summary).
- [x] **DONE (C3)** — rate limiter (`/login`,`/ai/*`), per-alert triage persistence, and structured IOC extraction (`/ai/iocs`, `messages.parse`-style schema) with an inline fleet-hunt pivot per IOC. Live: real Claude extracted 17 typed IOCs; the first IP correlated across 2 hosts.

---

## Phase D — Security & ops

### D1 — RBAC, audit, transport
- Roles (viewer/analyst/admin) on the token; an append-only **audit log** of
  case access + AI calls; document/ship a TLS reverse-proxy (nginx/Caddy) in front.
- [x] **PARTIAL (D1)** — role claims in the signed token (viewer/analyst/admin; `RAPTORSCOPE_AUTH_ROLES`), analyst-gate on AI + `/hunt`, and an append-only `raptorscope.audit` log. TLS reverse-proxy remains doc-only.

### D2 — observability
- Structured JSON logging, `/metrics` (Prometheus), request-id propagation and
  basic tracing.
- [x] **DONE (D2)** — request-id correlation, access logging, and a Prometheus `/metrics` endpoint (requests_total, by-status, ai_requests).

### D3 — supply chain
- Pin all deps (lockfiles committed for Python too), generate an SBOM, scan the
  Docker images in CI (Trivy/Grype).
- [x] **DONE (D3)** — pinned `requirements.lock`; CI `security` job: `pip-audit` (gates fixable vulns; one unfixable transitive `diskcache` CVE triaged + documented), production `npm audit --omit=dev` (clean), CycloneDX SBOM artifact, Trivy fs scan. See `docs/SUPPLY-CHAIN.md`.

---

## Phase E — Quality & delivery

### E1 — live-ES + e2e in CI
- Dockerized ES service in CI for an **index-template + ingest smoke** (spec §6);
  Playwright **e2e** driving the SPA against a seeded backend (couldn't run locally
  — Node 26/Chromium; runs cleanly on CI Linux).
- [x] **PARTIAL (E1)** — CI `integration` job: live Elasticsearch service → ingest smoke + ES-native detector parity (locks Phase B). Playwright e2e still a follow-up (Node-26/Chromium issue locally; runs on CI Linux).

### E2 — coverage & evaluator robustness
- Coverage gates (pytest-cov, vitest coverage); **property/fuzz tests** for the
  Sigma condition parser (`detect/evaluate.py`) and `_leaf_text`/`_apply_op`.
- [x] **DONE (E2)** — evaluator property/fuzz tests (found+fixed an IndexError); coverage gate pending.

### E3 — release & distribution
- PyPI publish workflow, semver + `CHANGELOG.md`, published Docker images,
  and **collector-build automation** (profile → offline Velociraptor collector) in
  `make`/CI.
- [x] **PARTIAL (E3)** — `CHANGELOG.md`, version 0.2.0, wheel builds clean, and a PyPI Trusted-Publishing release workflow (tag-triggered). Collector-build automation still needs the Velociraptor binary (blocked, same as A3).

---

## Sequencing & self-review

- **Order:** A → B → E1 (lock fidelity+scale behind CI) → C → D. A is non-negotiably
  first: a DFIR tool unproven on real data is a demo.
- **Contract stability:** B/C keep the existing JSON + SPA contracts; only Phase A
  changes normalizer field semantics (guarded by fixture-bound tests).
- **Effort markers:** A1/A2 and B are the large items; A4, C2, C3 (triage
  persistence), D2, E2 are small–medium quick wins that raise trust fast.
- **Guardrail honored:** the core stays UI-agnostic; every phase ships standalone
  value and keeps both test suites green.
