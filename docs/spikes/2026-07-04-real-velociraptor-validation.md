# Spike: validating normalizers against REAL Velociraptor output

**Date:** 2026-07-04 · **Method:** no execution. Velociraptor could not be run
here (auto-mode blocked fetching/executing an unsigned release binary, and
capturing this host's real data would leak personal info). Instead the synthetic
fixtures were validated against Velociraptor's **published artifact definitions**
(docs.velociraptor.app). This is the honest state of the fidelity gap.

## Headline finding

The Phase-1/2 fixtures are **synthetic and diverge from real Velociraptor
output** — three artifact *names* were invented, and several real artifacts emit
different *column* names. The pipeline is correct; the collection contract needs
reconciling with reality before a real capture will ingest cleanly.

## Artifact-by-artifact reality

| Raptorscope stem | Real artifact | Name? | Column deltas (real → ours) |
|---|---|---|---|
| `installed_apps` | **MacOS.System.Packages** | ✅ | `SignedBy`→`SignerCN`, `LastModified`→`Mtime`, `ObtainedFrom` (new), **no `BundleIdentifier`** |
| `tcc` | **MacOS.System.TCC** | ✅ | emits boolean **`Allowed`** (not `AuthValue` 0/2); also `User` |
| `quarantine` | **MacOS.System.QuarantineEvents** | ✅ | LSQuarantine* columns (schema to reconfirm on a real capture) |
| `processes` | **MacOS.Sys.Pslist** (alias of `Linux.Sys.Pslist`) | ⚠ name | `CreatedTime`→`Mtime`, **`Hash`** not `CodeSignature`, plus `RSS`/`Deleted` |
| `launch_items` / `login_items` / `cron_items` | **MacOS.Detection.Autoruns** (single artifact) | ❌ invented | per-*source* columns (`OSPath`, `LaunchdConfig`, `Program`, `Hash`, crontab `Minute/Hour/Command/…`, `LoginItemConfig`); **no flat `Label`/`ProgramArguments`/`RunAtLoad`/`CodeSignature`** |
| `config_profiles` | *(no standard built-in)* | ❌ | needs custom VQL (`profiles -C -o stdout-xml`) |
| `btm_items` | *(no standard built-in)* | ❌ | needs custom VQL over the BTM db |

## What was fixed now (tolerant normalizers)

The normalizers where the real schema is clean and confirmed now accept **both**
the synthetic and the real columns (`tests/normalize/test_real_columns.py`):

- **inventory** — reads `SignedBy`/`LastModified`/`ObtainedFrom` as well as the
  synthetic `SignerCN`/`Mtime`; `signed` derived from the signer string.
- **tcc** — reads the boolean `Allowed`, falling back to `AuthValue`.
- **processes** — reads `CreatedTime`, falling back to `Mtime`.

`ARTIFACT_ALIASES` now also maps the confirmed real names (`MacOS.Sys.Pslist`,
`MacOS.System.QuarantineEvents`, `MacOS.System.TCC`, `MacOS.System.Packages`).

## Remaining gap (tracked, NOT faked)

- **Persistence family rework:** `MacOS.Detection.Autoruns` is one artifact with
  per-source rows and nested config blobs (`LaunchdConfig`, `LoginItemConfig`),
  not the flat per-type fixtures we invented. Consuming it means: parse the
  nested plist config, derive `type` from the source/OSPath, and drop the invented
  `Label`/`ProgramArguments`/`RunAtLoad` in favor of what Autoruns actually emits
  (`Program`, `Hash`, crontab fields). This is a real mapper rewrite.
- **config_profiles / btm:** author custom VQL artifacts (no standard built-ins);
  then a matching mapper.
- **Signatures:** Autoruns/Pslist give a **`Hash`**, not a code-signature object —
  the `process.code_signature.*` mappings (and the unsigned-based detections) need
  a signature-enrichment step or a different signal for real captures.

## To finish for real

1. Build an offline collector from the reconciled `profile/` (Autoruns + Pslist +
   TCC + QuarantineEvents + Packages + custom profiles/BTM VQL).
2. Run it on a Mac → `Collection-<host>.zip`.
3. Replace the synthetic fixtures with trimmed **real** rows (sanitized of PII),
   updating the persistence mappers to the Autoruns shape.
4. Re-verify the paired detections against the real column values.
