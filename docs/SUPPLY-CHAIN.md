# Supply-chain security

Raptorscope pins its dependencies and scans them in CI (the `security` job).

## Pinning
- **Python** — `requirements.txt` states the top-level ranges; `requirements.lock`
  is the fully-resolved pin (generated with `pip-compile pyproject.toml`).
  Reproduce an install with `pip install -r requirements.lock`.
- **Web** — `web/package-lock.json` is committed; CI installs with `npm ci`.

## Scanning (CI `security` job)
- **`pip-audit`** on the Python deps — fails the build on any known-vulnerable,
  *fixable* dependency (see the triaged exception below).
- **`npm audit --omit=dev --audit-level=high`** on the **production** web deps
  (`dompurify`, `marked`, `react`, `react-dom`). The shipped artifact is the
  static `web/dist/` bundle — it contains no `node_modules`, so dev/build tooling
  CVEs (vite, vitest) are **not** in the deployed surface and do not gate release.
- **CycloneDX SBOM** generated and uploaded as a build artifact.
- **Trivy** filesystem scan of the repository.

## Triaged findings

| Finding | Component | Decision |
|---|---|---|
| **CVE-2025-69872** (pickle-deserialization RCE requiring attacker **write access to the DiskCache directory**) | `diskcache 5.6.3` — a **transitive** dep of `pySigma` (pinned `<6.0.0`; **no fixed version** exists) | **Accepted / ignored in CI** (`--ignore-vuln CVE-2025-69872`). Raptorscope invokes pySigma only to convert its **own trusted** Sigma rules; it does not expose the DiskCache directory to untrusted writers, so the attack precondition isn't reachable. Re-evaluate when pySigma allows `diskcache>=6`. |
| `vite` (high), `vitest` (critical), + 3 moderate | **dev/build tooling only** | Not shipped (static `dist/` bundle has no node deps). Tracked; not release-gating. Bump when a compatible fix lands. |

Everything **else** must be clean — the CI gates fail on any new fixable
vulnerability in a shipped dependency.
