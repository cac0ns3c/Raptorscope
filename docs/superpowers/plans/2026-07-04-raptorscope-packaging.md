# Raptorscope Packaging, Docs & Demo (Phase 5) Implementation Plan

**Goal:** Make the whole stack installable, runnable, and demonstrable by someone
who did not build it. Ship the Velociraptor **collection profile** (the collection
contract), teach the ingest path to accept **real Velociraptor artifact names**,
commit a **sample case + one-command demo**, and write **install/demo docs**.

**Spec reference:** design spec §9 phase 5 (collector build UX, install docs,
sample-case demo), §4 component 1 (collection profile), §8 (`profile/`).

**Architecture:** No new runtime components — this phase wires the existing core
into a distributable shape. The one code change is an **artifact-name → normalizer
alias** so a genuine Velociraptor collection zip (files named
`MacOS.System.TCC.json`, …) ingests without renaming, closing the loop between the
`profile/` artifact set and the CLI.

## Global Constraints

- Same as prior phases: SPDX headers, GPL-3.0-or-later, DCO sign-off, no live
  infra in tests.
- Do not disturb the dev servers already running for manual testing; any
  verification that needs a server uses a throwaway port.

---

### Task 1: Real-artifact ingest aliases + collection profile

- `src/raptorscope/collection.py`: add `ARTIFACT_ALIASES` mapping Velociraptor
  built-in artifact names → collection stems (from the spike notes), and resolve
  aliases when keying artifacts so both `tcc.json` and `MacOS.System.TCC.json`
  load as `tcc`. CLI `_NORMALIZERS` lookups go through the resolved name.
- `profile/raptorscope-macos.yaml`: the curated artifact set (the collection
  contract) — the nine `MacOS.System.*` artifacts, each annotated with the ECS
  dataset + normalizer it feeds.
- `profile/README.md`: how to build an offline collector / run as a server hunt
  from the profile, and how the output maps back to ingest.
- Tests: `tests/test_profile.py` — every artifact in the profile YAML resolves to
  a registered normalizer, and a collection whose files use real artifact names
  ingests to the same docs as the stem-named one.

### Task 2: Sample case + one-command demo

- `samples/mac-victim/`: a committed sample collection (the nine artifacts, real
  Velociraptor-style filenames) + `host.json`, built from the fixtures.
- CLI `demo` subcommand: `raptorscope demo [--port]` ingests the bundled sample
  into an in-memory store and serves the API (offline, no ES) — the zero-setup
  path behind the GUI.
- Tests: `tests/test_demo.py` — the sample collection loads to 22 docs across all
  five datasets; `build_demo_app()` serves `/cases` with the sample case and
  fires alerts.

### Task 3: Makefile + packaging polish

- `Makefile` targets: `setup` (venv + deps + editable install + `npm install`),
  `test` (pytest + web verify), `serve`, `web`, `demo`, `build-web`, `clean`.
- Confirm `pip install -e .` exposes the `raptorscope` console script (done) and
  that `python -m raptorscope` and the script are equivalent.
- Optional `docker-compose.yml` for a local single-node Elasticsearch (for the
  live-ES path), documented as opt-in.

### Task 4: Install & demo docs + README

- `docs/INSTALL.md`: prerequisites (Python 3.10+, Node), backend + web setup,
  running tests, the live-ES path.
- `docs/DEMO.md`: end-to-end walkthrough — `make demo`, open the SPA, follow an
  alert pivot-to-evidence on the sample case; and the real-collection path
  (build collector from `profile/`, collect on a Mac, ingest).
- Update `README.md`: mark Phase 5 done, link INSTALL/DEMO, add the `make demo`
  quickstart and the `profile/` collection contract.

## Self-review notes

- **Spec coverage:** collection profile (§4.1/§8) + collector build UX, sample-case
  demo, and install docs — all of §9 phase 5.
- **Closes the loop:** the alias map means the artifact set named in `profile/`
  actually ingests, so the profile is a real contract, not just documentation.
- **Verifiable here:** everything is Python/docs/config; the demo path is exercised
  by tests and a throwaway-port smoke, with no dependency on the running servers.
