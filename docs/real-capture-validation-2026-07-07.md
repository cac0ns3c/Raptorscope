# Real-data false-positive validation — 2026-07-07 (140-rule set)

After expanding the detection set to 140 rules, every rule was verified only against
*synthetic* hit/benign fixtures. This pass runs the full set against **real host
evidence** to find the false positives that only genuine data surfaces.

> Guardrail: no host data is committed — only aggregate counts, the one rule fix,
> and this summary. The captures stay in gitignored scratch and are discarded.

## Method

- **Live process + network state** of a real macOS dev machine: 476 processes
  (real argv via `ps -axww`) + 103 network endpoints (`netstat`). Code signatures
  were pinned to *trusted* so signature-gated rules stayed quiet — this isolates the
  `process.command_line` false-positive surface, where the argv-matching rules live.
- **Real evidence bundle**: a genuine capture (real `QuarantineEventsV2` → 135 rows,
  real `LaunchAgents` → 3, real `.logarchive` → 16 unified-log events) run through the
  normal ingestion path.

All 140 rules were evaluated against the normalized docs; every fire was triaged.

## Results

| Corpus | Docs | Fires | Rules firing | Genuine rule FPs |
|---|--:|--:|--:|--:|
| Live processes + network | 579 | 3 → **0** after fix | 1 → 0 | **1 (fixed)** |
| Real evidence bundle | 154 | 5 | 2 | 0 |

**One genuine false positive**, now fixed:

- **`macos_process_interpreter_inline_code`** fired 3× on routine shell plumbing —
  a login shell (`login … bash -c exec … zsh`) and shell-snapshot sourcing
  (`zsh -c source …`). Root cause: the `sh -c` token matched `zsh -c` / `bash -c` as
  a **substring** (z-`sh -c`, ba-`sh -c`), and bare shell `-c` is one of the most
  common benign patterns on macOS. Fix: the rule now keys only on *interpreted-
  language* inline execution (`python -c`, `ruby -e`, `perl -e`, `node -e`, `php -r`).
  Malicious shell one-liners remain covered by the reverse-shell, network-command,
  and base64-exec rules, which key on the payload rather than the `-c` flag. After the
  fix: **0 fires** on the 476 live processes.

**The 5 bundle fires were both rules working correctly, not FPs:**

- `macOS persistence program in suspicious path` (3×) — the `LaunchAgents` plists were
  staged under `/private/tmp/…` for the test bundle, so their path legitimately looked
  like a temp-dir persistence item. On a real disk-image ingestion these live at
  `~/Library/LaunchAgents` and would not fire. A staging artifact, not a rule defect.
- `macOS non-Apple client requested a sensitive TCC service` (2×) — correctly flagged a
  non-Apple binary under `~/.local` requesting a sensitive TCC service. This is exactly
  the signal the rule is for; an analyst dispositions it as benign (it's the endpoint
  tooling), but the detection firing is correct.

## Signature surface (follow-up pass)

The run above pinned signatures to *trusted*, so the six signature-gated rules
(`macos_process_unsigned`, `..._suspicious_path`, `..._removable_media_execution`,
and three persistence rules) weren't exercised. This follow-up captured **real
`codesign` verdicts** for every running process — Trusted = a real signing Authority
(Apple / Developer ID), ad-hoc (Authority=None) counted as untrusted, matching the
collector's `TrustedSigner` semantics.

- 386 processes resolved to a real executable file: **380 trusted, 6 untrusted**
  across just **3 distinct binaries** — all Homebrew ad-hoc-signed (`node`, `python`,
  `limactl`) under `/opt/homebrew`.
- **0 fires.** `macos_process_unsigned` already carries a `filter_dev` excluding
  `/opt/homebrew`, `/usr/local/Cellar`, `/usr/local/bin`, so the ad-hoc Homebrew
  binaries — the dominant benign source of "untrusted" on a dev Mac — are correctly
  suppressed. The other five signature rules need a second condition (suspicious path,
  removable volume, persistence context) none of the real processes met.

(Method note: macOS `ps -o comm` truncates paths, and a truncated path that resolves
to a *directory* makes `codesign` report "unsigned" — an early version of this pass
showed 7 phantom `/System/Library/` fires from exactly that. Restricting to real
executable *files* removed them. A reminder that the capture harness, not just the
rules, has to be validated.)

## Takeaway

Across ~1,100 real docs spanning six datasets — including genuine per-process code
signatures — the 140-rule set produced **one** genuine false positive (a substring bug,
fixed) and was otherwise silent or correctly flagging. The command-line rules'
multi-token / `filter_*` tightening and the signature rules' dev-prefix filter both
held up on real host state. The detection set is now real-data-validated across every
dataset it can see.
