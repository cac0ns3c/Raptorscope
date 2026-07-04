# Raptorscope macOS collection profile

`raptorscope-macos.yaml` is the **collection contract**: the curated set of
Velociraptor `MacOS.System.*` artifacts that the normalizers map to ECS and that
the paired Sigma detections run against. If an artifact is added here, it needs a
normalizer and a detection (enforced by `detect/pairing.py`); nothing in the
profile is collected "for free."

## What it collects

The nine artifacts answer the macOS first-hour triage questions:

| Question | Artifact(s) |
|----------|-------------|
| who's persisting | LaunchServices, LoginItems, Crontab, Profiles, BackgroundTaskManagement |
| what ran | Processes |
| what got in | QuarantineEvents |
| what got permission | TCC |
| what's installed | Packages |

## Build an offline collector

Velociraptor can package a profile into a standalone, single-host collector
binary that writes a results zip — no server required:

```bash
# using a Velociraptor binary with the built-in MacOS.System.* artifacts
velociraptor collector \
  --artifacts MacOS.System.LaunchServices,MacOS.System.LoginItems,\
MacOS.System.Crontab,MacOS.System.Profiles,MacOS.System.BackgroundTaskManagement,\
MacOS.System.Processes,MacOS.System.QuarantineEvents,MacOS.System.TCC,MacOS.System.Packages \
  --output Collection-<host>.zip
```

Run the collector on the target Mac; it produces `Collection-<host>.zip`.

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
