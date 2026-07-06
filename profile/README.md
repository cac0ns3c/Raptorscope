# Raptorscope macOS collection profile

`raptorscope-macos.yaml` is the **collection contract**: the curated set of
Velociraptor artifacts — built-in (`MacOS.System.*`, `MacOS.Detection.Autoruns`)
plus custom VQL (`MacOS.Raptorscope.*`) — that the normalizers map to ECS and that
the paired Sigma detections run against. If an artifact is added here, it needs a
normalizer and a detection (enforced by `detect/pairing.py`); nothing in the
profile is collected "for free."

## What it collects

The eight artifacts (4 built-in + 4 custom) answer the macOS first-hour triage
questions. Config profiles, BTM, code-signature-enriched processes, and netstat
have no adequate built-in, so raptorscope ships custom VQL under `custom-vql/`:

| Question | Artifact | Source |
|----------|----------|--------|
| who's persisting (launch agents/daemons, login items, cron) | `MacOS.Detection.Autoruns` | built-in |
| who's persisting (config / MDM profiles) | `MacOS.Raptorscope.ConfigProfiles` | custom VQL |
| who's persisting (Background Task Management) | `MacOS.Raptorscope.BTM` | custom VQL |
| what ran (with code-signature trust) | `MacOS.Raptorscope.SignedProcesses` | custom VQL |
| what got in | `MacOS.System.QuarantineEvents` | built-in |
| what got permission | `MacOS.System.TCC` | built-in |
| what's installed | `MacOS.System.Packages` | built-in |
| what it's talking to (listeners + connections) | `MacOS.Raptorscope.Netstat` | custom VQL |

The contract of record is `raptorscope-macos.yaml`. (`custom-vql/` also carries
`MacOS.Raptorscope.SignedAutoruns`, a per-signature alternative to the built-in
Autoruns that the contract does not currently use.)

## Build an offline collector

Velociraptor can package a profile into a standalone, single-host collector
binary that writes a results zip — no server required:

```bash
# -D loads the custom MacOS.Raptorscope.* VQL; the rest are built in.
velociraptor -D profile/custom-vql collector \
  --artifacts MacOS.Detection.Autoruns,MacOS.Raptorscope.ConfigProfiles,\
MacOS.Raptorscope.BTM,MacOS.Raptorscope.SignedProcesses,MacOS.System.QuarantineEvents,\
MacOS.System.TCC,MacOS.System.Packages,MacOS.Raptorscope.Netstat \
  --output Collection-<host>.zip
```

Run the collector on the target Mac; it produces `Collection-<host>.zip`. Note
that TCC needs Full Disk Access granted to the Velociraptor client binary, and
BTM/ConfigProfiles want the client running with root privileges.

## Run as a server hunt

Alternatively, schedule the same artifact set as a hunt from a Velociraptor
server across enrolled macOS hosts — the per-host output is identical.

## Ingest the result

The collector/hunt writes one JSON result per artifact, named by artifact
(`MacOS.System.TCC.json`, …). Raptorscope aliases those names to its normalizers
(`raptorscope.collection.ARTIFACT_ALIASES`), so a collection ingests directly:

```bash
raptorscope ingest Collection-<host>.zip                 # dry-run doc count
raptorscope ingest Collection-<host>.zip --es http://localhost:9200
```

Add a `host.json` (`{"name": "...", "os": {"type": "macos"}}`) to the collection
for `host.*`/`user.*` context. See `samples/mac-victim/` for a worked example and
`docs/DEMO.md` for the end-to-end walkthrough.
