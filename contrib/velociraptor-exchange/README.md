# Velociraptor Artifact Exchange — submission package

**Submitted:** [Velocidex/velociraptor-docs#1284](https://github.com/Velocidex/velociraptor-docs/pull/1284)
(all four artifacts, awaiting review).

Exchange-ready copies of Raptorscope's four custom macOS VQL artifacts, contributed
to the **Velociraptor Artifact Exchange**
([`Velocidex/velociraptor-docs`](https://github.com/Velocidex/velociraptor-docs),
`content/exchange/artifacts/`).

These are derived from `profile/custom-vql/` with the raptorscope-internal bits
removed so they stand alone: the GPL SPDX header and build comments are dropped and
the "consumed by `normalize_*`" notes are stripped. **The VQL query bodies are
byte-identical to the in-repo artifacts** — only metadata/comments differ.

| Artifact | What it collects | Real-data validated |
|---|---|---|
| `MacOS.Raptorscope.SignedProcesses` | processes + code-signature trust (`codesign`) | ✅ 489 rows; every row enriched; 3 untrusted flagged |
| `MacOS.Raptorscope.BTM` | Background Task Management persistence (`sfltool dumpbtm`) | ✅ 7 items; correct disposition/paths |
| `MacOS.Raptorscope.Netstat` | socket table + owning process (`netstat()` + Pslist) | ✅ 66 rows |
| `MacOS.Raptorscope.ConfigProfiles` | installed config/MDM profiles (`profiles show`) | ⏳ verify-passes; parse logic validated on a schema-accurate sample, **not yet on a populated/managed host** |

All four pass `velociraptor artifacts verify`. `SignedProcesses` and `Netstat`
depend only on the built-in `MacOS.Sys.Pslist`.

## Submitting the PR

```bash
gh repo fork Velocidex/velociraptor-docs --clone
cd velociraptor-docs
git checkout -b macos-raptorscope-artifacts
cp <raptorscope>/contrib/velociraptor-exchange/MacOS.Raptorscope.*.yaml content/exchange/artifacts/
git add content/exchange/artifacts/MacOS.Raptorscope.*.yaml
git commit -m "Add MacOS.Raptorscope.{SignedProcesses,BTM,Netstat,ConfigProfiles}"
git push -u origin macos-raptorscope-artifacts
gh pr create --repo Velocidex/velociraptor-docs --fill
```

## Open questions to resolve before / during review

1. **Naming.** 25 of 26 existing macOS Exchange artifacts use functional-category
   names (`MacOS.Network.*`, `MacOS.System.*`, `MacOS.Sys.*`), not a vendor segment.
   `MacOS.Raptorscope.*` is valid but an outlier; reviewers may ask to rename to
   e.g. `MacOS.Network.Netstat`, `MacOS.System.BackgroundTaskManagement`,
   `MacOS.Sys.SignedProcesses`, `MacOS.System.ConfigurationProfiles`. Renaming is a
   trivial follow-up (change `name:` + filename).
2. **Licensing.** The GPL-3.0 SPDX header was removed for the Exchange copies; the
   docs repo carries its own contribution license. Confirm the project's licensing
   expectations before submitting.
3. **ConfigProfiles.** Field mapping follows Apple's documented `profiles` plist
   schema; it has not been confirmed against a host with profiles installed. Either
   note this in the PR or hold it for a follow-up once validated on a managed host.
4. **GUI reformat.** The contribution guide suggests running artifacts through the
   GUI's "Reformat VQL" before submission — do a pass if a server/GUI is available.
