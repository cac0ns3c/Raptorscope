# Custom Velociraptor artifacts

These are the collection artifacts Raptorscope ships for macOS telemetry that has
no suitable first-party built-in. Each is authored to the Velociraptor
[artifact-contribution guidelines](https://www.velociraptor-docs.org/dev/contributing-artifacts/)
so they can be dropped into a Velociraptor server (or submitted to the Exchange)
as-is.

| Artifact | Emits | raptorscope stem |
|---|---|---|
| `MacOS.Raptorscope.ConfigProfiles` | installed config/MDM profiles + signing | `config_profiles` |
| `MacOS.Raptorscope.BTM` | macOS 13+ Background Task Management items | `btm_items` |
| `MacOS.Raptorscope.SignedProcesses` | Pslist + per-process code-signature trust | `processes` |
| `MacOS.Raptorscope.SignedAutoruns` | Autoruns + per-item code-signature trust | `autoruns` |
| `MacOS.Raptorscope.Netstat` | live TCP/UDP sockets + owning process | `network` |

## Conformance

Each artifact follows the guidelines:

- **Naming** — `MacOS.Raptorscope.<Component>` (OS.Namespace.Component); the `name`
  matches the filename and the `artifact:` key in `profile/raptorscope-macos.yaml`.
- **Description** — a lead sentence (never "This artifact…"), search keywords, a
  `### Output` section, and the MITRE technique(s).
- **`author` + `reference`** — attribution (anonymized GitHub identity) and external
  references (MITRE + a topical source).
- **`type: CLIENT`** and a **named source** with a **`precondition`**
  (`SELECT OS FROM info() WHERE OS = 'darwin'`) so the artifact is skipped on
  non-macOS endpoints.
- **`column_types`** typing the timestamp columns.

`tests/test_custom_vql.py` lints these statically (a proxy for
`velociraptor artifacts verify`, which needs the Velociraptor binary) and checks
that the profile's `custom_vql` paths resolve to the named artifacts.

## Before contributing upstream

1. Load the artifact in the Velociraptor GUI editor and click **Reformat VQL**.
2. Run `velociraptor artifacts verify <file>.yaml` — the Exchange CI rejects
   artifacts that fail static analysis.
3. Exchange artifacts live under
   `velociraptor-docs/content/exchange/artifacts` (PR); built-ins additionally
   need automated tests in the Velociraptor repo's `testdata`.

> Note: Raptorscope's **detections** are Sigma rules (`detections/sigma/`), which
> have their own upstream home — the
> [Velociraptor Sigma Rules project](https://github.com/Velocidex/velociraptor-sigma-rules) —
> rather than the artifact Exchange.
