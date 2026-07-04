# Raptorscope GUI (Phase 4) Implementation Plan

**Goal:** Ship the v1 React/TypeScript SPA — the dedicated macOS triage
experience — consuming the Phase-3 query API. Analyst can load a case, read the
first-hour overview, browse per-artifact views, scan a unified timeline, and
triage detection alerts with pivot-to-evidence.

**Spec reference:** design spec §5b (GUI scope items 1–5), §7 (React + TS SPA),
§8 (`web/`). Phasing step 4.

**Architecture:** A Vite + React + TypeScript SPA under `web/`. A typed
`ApiClient` (`api/client.ts`) is the sole data source; it is provided via React
context (`ApiProvider`) so component/interaction tests inject a **fake client**
seeded with fixture-shaped data — the same dependency-injection seam the backend
used for its `Store`, so the whole GUI is testable with **no network and no live
API**. View state (selected case + active tab) is lightweight in-app state; no
router dependency. Tests: Vitest + React Testing Library + jsdom.

**Tech stack (new, all under `web/`, isolated from the Python project):**
`react`, `react-dom`, `typescript`, `vite`, `@vitejs/plugin-react`, `vitest`,
`@testing-library/react`, `@testing-library/user-event`, `@testing-library/jest-dom`,
`jsdom`.

## Global Constraints

- SPDX header (`// SPDX-License-Identifier: GPL-3.0-or-later`) on every `.ts`/`.tsx`.
- The SPA depends only on the Phase-3 JSON contracts; it never talks to ES or the
  normalizers directly (keeps the core UI-agnostic per spec §3).
- Component/interaction tests take **no network** (fake client). `npm test` and
  `npm run build` (tsc + bundle) must both pass — the CI-equivalent verification.
- `web/` has its own `node_modules`/`dist` (gitignored); the Python `.venv` and
  tests are unaffected.

## API contract consumed (from Phase 3)

`GET /cases` → `Case[]`; `/cases/{c}/overview` → `Overview`;
`/cases/{c}/artifacts/{dataset}?limit&offset` → `{dataset,total,items:Doc[]}`;
`/cases/{c}/timeline?limit` → `TimelineRow[]`; `/cases/{c}/alerts` → `Alert[]`.

---

### Task 1: Scaffold `web/` + tooling + smoke test

- `web/package.json` (scripts: `dev`, `build`, `test`, `typecheck`), `tsconfig.json`,
  `tsconfig.node.json`, `vite.config.ts` (react plugin + vitest jsdom + setup),
  `index.html`, `src/main.tsx`, `src/App.tsx` (renders app title), `src/test/setup.ts`
  (jest-dom), `.gitignore` (`node_modules/`, `dist/`).
- Update root `.gitignore` for `web/node_modules`, `web/dist`.
- Test `src/test/App.test.tsx`: App renders the "Raptorscope" heading.
- Gate: `npm install`, `npm test`, `npm run build` all green.

### Task 2: API types + client + fake client

- `src/api/types.ts`: `Case`, `Overview`, `Doc`, `ArtifactPage`, `TimelineRow`,
  `Alert` (mirror Phase-3 JSON).
- `src/api/client.ts`: `ApiClient` interface + `createHttpClient(baseUrl)` (fetch).
- `src/context/ApiContext.tsx`: `ApiProvider` + `useApi()` hook.
- `src/test/fakeClient.ts`: in-memory `ApiClient` seeded with a dirty case + a
  clean case (mirrors the backend seed) for all tests.
- Test: `createHttpClient` builds correct URLs (mock `fetch`); fake client returns
  seeded cases.

### Task 3: CasePicker (load/select a case)

- `src/components/CasePicker.tsx`: lists cases (name, doc_count, datasets),
  calls `onSelect`. Loading + empty states.
- Test: renders both seeded cases; clicking one fires `onSelect` with its name.

### Task 4: Overview dashboard

- `src/components/Overview.tsx`: dataset count tiles, persistence-type breakdown,
  unsigned process/app counters, total.
- Test: shows dataset counts and persistence-type rows from the fake overview.

### Task 5: ArtifactTable (per-artifact views)

- `src/components/ArtifactTable.tsx`: given a case + dataset, fetches the page and
  renders a dataset-appropriate column set (persistence/process/quarantine/tcc/
  inventory); pagination controls.
- Test: renders rows for `macos.persistence`; switching dataset refetches; next
  page advances offset.

### Task 6: Timeline

- `src/components/Timeline.tsx`: newest-first rows (timestamp, dataset badge,
  summary). 
- Test: rows render in the API order; dataset badges present.

### Task 7: Alerts + pivot-to-evidence

- `src/components/Alerts.tsx`: alert list (level badge, title, dataset, evidence);
  clicking an alert calls `onPivot(dataset, doc_id)` (pivot-to-evidence).
- Test: renders seeded alerts sorted by level; clicking fires `onPivot` with the
  alert's dataset + doc_id; benign case shows an empty state.

### Task 8: App shell wiring + integration test + docs

- `src/App.tsx`: case picker → workspace with tabs (Overview / Artifacts /
  Timeline / Alerts); alert pivot deep-links into the Artifacts tab for that
  dataset. `ApiProvider` wraps the app; dev uses `createHttpClient` with a
  `VITE_API_BASE` (Vite proxy `/api` → `http://127.0.0.1:8000`).
- Integration test (fake client): select case → see overview → open Alerts →
  click an alert → lands on Artifacts for that dataset.
- Update `README.md` (web/ dev usage: `npm install`, `npm run dev`, `npm test`;
  run alongside `raptorscope serve`). Mark Phase 4 done.
- Gate: `npm test` + `npm run build` green.

## Self-review notes

- **Spec coverage:** Tasks 3–7 are GUI scope §5b items 1–5 one-for-one; Task 8
  wires them and implements pivot-to-evidence end-to-end.
- **Testable without infra:** the `ApiClient` context seam keeps every test on the
  fake client; `npm run build` gives the typecheck/bundle guarantee. A live smoke
  against `raptorscope serve` is documented but not required for green.
- **Decoupled:** SPA consumes only Phase-3 JSON; Python side untouched.
