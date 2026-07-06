# Real-capture validation — 2026-07-05

The first end-to-end run of the pipeline against a **real** macOS host (not
synthetic fixtures), using Velociraptor **v0.77.1**. This is the validation that
had been blocked all along — the binary is now installed. No personal capture data
is committed; the collection lives only in gitignored scratch. What's recorded here
is aggregate counts, column names, and the fixes the real data drove.

## Collected (built-ins + custom VQL)

| Artifact | Rows | Notes |
|---|---:|---|
| `MacOS.Sys.Pslist` | 484 | real processes |
| `MacOS.Detection.Autoruns` | 894 | real persistence |
| `MacOS.System.QuarantineEvents` | 135 | real downloads |
| `MacOS.System.Packages` | 319 | installed apps |
| `MacOS.Raptorscope.Netstat` | 66 | after the fix (0 before) |
| `MacOS.System.TCC` | **0** | needs Full Disk Access for the collector |
| `MacOS.Raptorscope.ConfigProfiles` | **0** | `/var/db/ConfigurationProfiles/Store` is SIP/perm-protected |
| `MacOS.Raptorscope.BTM` | **hung** | `sfltool dumpbtm` did not return (needs privileges / a timeout) |

Ingested: **1898 docs** through the normalizers + 38 detections.

## Pipeline bugs the real data exposed (fixed)

1. **`normalize_inventory` crashed** — real `MacOS.System.Packages` emits `SignedBy`
   as a **cert-chain list** (leaf-first), not a string; `signer not in _UNSIGNED`
   raised `unhashable type: 'list'`. Fixed to take the leaf authority. Also
   confirmed real Packages has **no `BundleIdentifier`** (validates the earlier
   drop of the bundle-id rule).
2. **`@timestamp` empty on every process** — real `MacOS.Sys.Pslist` emits
   **`CreateTime`**; the normalizer only looked for `Mtime`/`CreatedTime`. Fixed.
3. **`MacOS.Raptorscope.Netstat` collected 0 rows** — three real-vs-assumed
   mismatches: `Family`/`Type` are **integers** (`2`/`1`), the string forms are
   `FamilyString`/`TypeString` (`IPv4`/`TCP`); `Status` is **`ESTAB`** not
   `ESTABLISHED`; and `netstat()` carries **no process name** (only `Pid`). Fixed
   the artifact to use the *String forms and resolve `Name`/`Exe` via a Pslist
   join. Re-verified with `velociraptor artifacts verify` (clean) and re-collected
   → 66 rows.

Each is now guarded by a regression test in `tests/normalize/test_real_columns.py`.

## False-positive rate on a clean host: 14 → 3

`raptorscope detect` on this (normal, uncompromised) Mac — every fire is a
candidate FP. Root causes, and the two tunings applied:

| Rule | Before | Root cause | Action | After |
|---|---:|---|---|---:|
| unsigned app outside `/Applications` | 7 | fired on `/System/Library`, `/Library/Application Support`, `~/Library` bundles Packages reports without a Developer-ID signer | exclude any `/Library/` path (malware drops land in Downloads/tmp/Shared) | 0 |
| process from a suspicious path | 4 | the `command_line` `/tmp/` branch — real processes reference `/tmp/` in argv | drop `/tmp/` from that branch (keep executable-path detection) | 0 |
| interpreter executing inline code | 2 | legit `zsh -c` / Homebrew `python` — inline `-c`/`-e` is ubiquitous | left as a documented noisy `experimental` rule (don't overfit to one host) | 2 |
| persistence program in suspicious path | 1 | one launch item referencing a staging path | left; 1/894 is acceptable for a high-signal rule | 1 |

Both tunings keep the paired fixtures green (malicious fires, benign silent).

## Operational findings (collection, not the pipeline)

- **TCC and ConfigProfiles need privileged/FDA collection** — as a normal user the
  collector gets 0 rows (TCC.db and the profile store are protected). A real
  deployment runs the Velociraptor client with the right entitlement.
- **`sfltool dumpbtm` hung** — the BTM artifact needs a bounded timeout and likely
  elevation; treat as needs-work for real use.
- **`netstat()` gives no process name** — resolved via a Pslist join, but that
  makes the artifact depend on Pslist being collectable.

## Privileged re-run (TCC / ConfigProfiles / BTM)

A second pass with `sudo` (root) to collect the three that came back empty. Result:
**still 0 rows for all three** — and the reasons are now confirmed, not guessed:

- **TCC** — `MacOS.System.TCC` opens `…/com.apple.TCC/TCC.db` with `sqlite()`. The
  user TCC.db exists and is owner-readable, but **TCC protects TCC.db from every
  process without Full Disk Access, root included.** `sudo` does not help; the
  Velociraptor *binary* must be granted FDA (System Settings → Privacy & Security →
  Full Disk Access, or a PPPC/MDM profile in a real fleet). This is the standard
  Velociraptor deployment requirement.
- **ConfigProfiles** — `/var/db/ConfigurationProfiles/Store` is SIP-protected even
  from root.
- **BTM** — `sfltool dumpbtm` **hangs** (verified interactively: 40s+ with no
  output), independent of privilege. The 30s background-kill added to the artifact
  is the right mitigation (it degrades to empty instead of stalling the whole
  collection), but real BTM coverage needs a different source than `sfltool` on
  this macOS build.

**Bottom line:** 5 of 8 collectors are validated on real data; the remaining 3 are
gated by macOS protections (FDA/SIP) or broken host tooling (`sfltool`), not by the
pipeline. Validating TCC on real data is a one-time FDA grant away; ConfigProfiles
and BTM need a privileged/alternate collection method.

## Guardrail

No process list, app inventory, quarantine URL, IP, username, or path from the real
host is committed. Only the *fixes* (normalizers, the Netstat artifact, two rule
tunings), synthetic regression tests mimicking the real column shapes, and this
aggregate summary. The capture stays in gitignored scratch and is discarded.
