# Security review — API auth, query, docs, ES (2026-07-04)

Focused review of the security-sensitive surface added after the v1 build:
optional auth, the search endpoint, the docs endpoint, the ES store, and the
SPA's markdown rendering. Raptorscope is a defensive DFIR tool that only reads
collected evidence.

## Findings

| # | Area | Severity | Finding | Resolution |
|---|------|----------|---------|------------|
| 1 | `api/auth.py` | **Medium** | Token HMAC secret defaulted to the constant `"raptorscope"`, so with auth enabled via env, tokens were forgeable by anyone who knew the (open-source) scheme. | **Fixed** — `from_env()` now uses `RAPTORSCOPE_AUTH_SECRET` if set, else a per-process `secrets.token_hex(32)`. Tokens reset on restart (they expire anyway). Test added. |
| 2 | `api/docs.py` | Info (safe) | `GET /docs/{id}` reads files from disk. Verified **no path traversal**: `id` only indexes a fixed whitelist (`_BY_ID`); the filesystem path comes from a constant map, never from user input. | No change. |
| 3 | `es/store.py`, `api/app.py` search | Info (safe) | User-supplied `host`/`dataset`/`field`/`value` reach ES as **term-filter values** (parameterized by the ES client) and Python-side `dig`/compare — not concatenated into query strings. No query injection. | No change. |
| 4 | `api/app.py` `/login` | Info (safe) | Invalid user and invalid password both return the same `401` via `token_for → None`; `hmac.compare_digest` used for constant-time credential comparison. No user enumeration / timing oracle. | No change. |
| 5 | `components/Docs.tsx` | Low (accepted) | `dangerouslySetInnerHTML` renders `marked` output. Content is **first-party repo docs** served by our own backend (same trust as app source), never user/ES data. | Accepted + commented. If docs ever include untrusted content, add DOMPurify. |
| 6 | SPA token storage | Low (accepted) | Bearer token is kept in `localStorage`; an XSS would expose it. Mitigated by same-origin serving, no third-party scripts, and short token TTL. | Accepted; documented. |
| 7 | Transport | Low (documented) | Credentials + tokens travel in the request; ES compose runs with security disabled. | **Documented** — run behind an HTTPS reverse proxy; compose is local-dev only (README + `docs/INSTALL.md`). |

## Not in scope / by design

- No rate-limiting on `/login` — acceptable for a single/small-team local tool;
  add a proxy-level limiter for exposed deployments.
- Auth is **off by default** so the offline demo needs no setup; enabling it is an
  explicit opt-in (`--auth-user/--auth-pass` or env).

## Verdict

One medium finding (forgeable-token default secret) fixed; the rest are safe or
accepted-and-documented. No injection, traversal, or enumeration issues found.
