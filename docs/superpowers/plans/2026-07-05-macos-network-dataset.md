# Plan — `macos.network` dataset (host network connections)

**Goal:** add a sixth ECS dataset, `macos.network`, giving Raptorscope its first
visibility into what a host is *talking to* (listeners + established connections),
not just its point-in-time state. Closes the biggest coverage blind spot (C2,
exfil, reverse/bind shells, lateral movement) and amplifies the existing IOC hunt
and timeline. Mirrors the established pattern: Velociraptor source → `normalize/*`
→ ECS → ES/in-memory → paired Sigma detections → tests.

Status: spec. Depends on nothing already shipped; additive.

---

## 1. Collection source

Primary: the Velociraptor `netstat()` VQL plugin, wrapped in a custom artifact for
consistency with the existing custom-VQL pattern (`profile/custom-vql/`). netstat
gives socket→owner without extra tooling; `lsof` is a later enrichment for the few
sockets netstat can't attribute.

`profile/custom-vql/MacOS.Raptorscope.Netstat.yaml` (sketch):

```yaml
name: MacOS.Raptorscope.Netstat
description: |
  Host TCP/UDP connections (listeners + established) with owning process — the
  network side of triage (reverse/bind shells, C2, exfil). Alias to the `network`
  stem.
type: CLIENT
sources:
  - query: |
      SELECT Pid, Name, Family, Type, Status,
             Laddr.IP AS LocalIP, Laddr.Port AS LocalPort,
             Raddr.IP AS RemoteIP, Raddr.Port AS RemotePort
      FROM netstat()
      WHERE Family =~ "INET"   -- IPv4/IPv6 only; drop unix sockets
```

Raw columns consumed by the normalizer: `Pid, Name, Family, Type, Status,
LocalIP, LocalPort, RemoteIP, RemotePort`.

`ARTIFACT_ALIASES` (src/raptorscope/collection.py): `"MacOS.Raptorscope.Netstat":
"network"`. (Real built-in `netstat()` has no first-party artifact name; if a
future Velociraptor build ships `MacOS.Network.Netstat`, add that alias too.)

## 2. ECS mapping — `normalize/network.py`

netstat is point-in-time **state**, not an event stream: there is no per-connection
timestamp, so `@timestamp` = collection time and provenance is stamped
`raptorscope.time.source = "collection"` (reuse the autoruns/processes provenance
pattern, not a fake event time).

| Raw column   | ECS field                         | Notes |
|--------------|-----------------------------------|-------|
| `RemoteIP`   | `destination.ip`                  | absent for LISTEN sockets |
| `RemotePort` | `destination.port` (long)         | absent for LISTEN sockets |
| `LocalIP`    | `source.ip`                       | |
| `LocalPort`  | `source.port` (long)              | the listening port on LISTEN sockets |
| `Type`       | `network.transport`               | `tcp` / `udp` (lower-cased) |
| `Family`     | `network.type`                    | `ipv4` / `ipv6` |
| `Status`     | `raptorscope.network.state`       | `LISTEN` / `ESTABLISHED` / … (keyword) |
| `Pid`        | `process.pid` (long)              | socket owner |
| `Name`       | `process.name`                    | socket owner |
| derived      | `network.direction`               | `ingress` for LISTEN; `egress` for ESTABLISHED with a non-loopback RemoteIP; else `internal` |
| derived      | `destination.address`             | copy of `destination.ip` so IOC hunt (substring) matches literal-IP indicators |

Sketch (mirrors `normalize/tcc.py`):

```python
from .ecs import ecs_base

_LOOPBACK = ("127.", "::1", "0.0.0.0", "::")

def normalize_network(rows, host):
    docs = []
    for r in rows:
        state = (r.get("Status") or "").upper()
        rip = r.get("RemoteIP") or ""
        doc = ecs_base(host, "macos.network")
        doc["@timestamp"] = host.get("collected_at") or ""      # collection time
        doc["raptorscope"] = {"time": {"source": "collection"},
                              "network": {"state": state}}
        net = {"transport": (r.get("Type") or "").lower(),
               "type": "ipv6" if "6" in (r.get("Family") or "") else "ipv4"}
        if r.get("LocalIP") is not None:
            doc["source"] = {"ip": r.get("LocalIP"), "port": r.get("LocalPort")}
        if rip:
            doc["destination"] = {"ip": rip, "address": rip,
                                  "port": r.get("RemotePort")}
        if state == "LISTEN":
            net["direction"] = "ingress"
        elif rip and not rip.startswith(_LOOPBACK):
            net["direction"] = "egress"
        else:
            net["direction"] = "internal"
        doc["network"] = net
        if r.get("Pid"):
            doc["process"] = {"pid": r.get("Pid"), "name": r.get("Name")}
        docs.append(doc)
    return docs
```

Register in the CLI `_NORMALIZERS` registry alongside the other `normalize_*`.

## 3. ES index template (`es/template.py`)

Add correctly-typed top-level `source`/`destination`/`network` objects and the
`raptorscope.network` sub-object (append to the existing `properties`):

```python
"source": {"properties": {"ip": {"type": "ip"}, "port": {"type": "long"}}},
"destination": {"properties": {
    "ip": {"type": "ip"}, "address": {"type": "keyword"}, "port": {"type": "long"}}},
"network": {"properties": {
    "transport": {"type": "keyword"}, "type": {"type": "keyword"},
    "direction": {"type": "keyword"}}},
# under raptorscope.properties:
"network": {"properties": {"state": {"type": "keyword"}}},
```

`destination.ip`/`source.ip` as ES `ip` type enables CIDR/range queries later.
`destination.address` is `keyword` so the substring IOC hunt works on it.

## 4. IOC hunt + timeline payoff

- **Hunt:** append `"destination.address"` (and optionally `"destination.ip"`) to
  `_INDICATOR_FIELDS` (src/raptorscope/api/store.py). An IP hunt like `45.9.148.99`
  then hits the *real connection*, not only the quarantine URL — the analyst payoff.
- **Timeline:** network docs already carry `@timestamp` + a `network.direction`
  badge; the SPA timeline renders them with the same provenance mtime/collection
  marker. Add a `Network` dataset tile to the overview (color like the others).
- **Overview:** `macos.network` counts + a "listeners owned by non-system binaries"
  signing-integrity-style panel.

## 5. Detections (first batch — paired hit + benign fixtures)

Focus on the gold-standard, low-FP signals; avoid port-only heuristics (noisy).

1. **`macos_network_shell_listener`** — a shell/interpreter bound to a listening
   socket = bind shell. `process.name` in `[bash, sh, zsh, nc, ncat, python,
   python3, perl, ruby, socat]` AND `raptorscope.network.state: LISTEN`. T1071 /
   T1059. Benign: `mDNSResponder`/`launchd`/`rapportd` listeners.
2. **`macos_network_shell_egress`** — a shell/interpreter with an established
   outbound connection = reverse shell. same process list AND `network.direction:
   egress`. T1571 / T1059.004. Benign: `curl`/`ssh` are not in the list; a user
   running `python` that connects out is the documented FP → require the process
   list to stay tight and mark experimental.
3. **`macos_network_egress_from_staging_path`** — a process whose executable lives
   in `/tmp` / `/private/tmp` / `/Users/Shared` with any egress connection = dropped
   binary phoning home. Needs `process.executable` on the row → enrich the netstat
   VQL with the exe path (foreach + `process_tracker`/`lsof`), or correlate to the
   `macos.process` dataset at query time. T1105 / T1571.
4. **`macos_network_listener_high_port_nonsystem`** — LISTEN on a non-ephemeral,
   non-standard port owned by a process outside `/System`/`/usr/libexec` (needs the
   exe enrichment from #3). Lower priority; higher FP — ship `medium`, experimental.

Rules 3–4 depend on adding `process.executable` to the netstat feed (lsof/exe
enrichment). Ship 1–2 first (they only need `process.name` + state), add 3–4 with
the enriched VQL.

## 6. Fixtures & tests

`fixtures/velociraptor/network.raw.json`:
- benign `[0]` `mDNSResponder` LISTEN :5353; `[1]` `Safari` ESTABLISHED →
  `17.253.x.x:443`; `[2]` `launchd` LISTEN :22.
- malicious `[3]` `bash` LISTEN :4444 (bind shell); `[4]`
  `/private/tmp/.cache/helper` ESTABLISHED → `45.9.148.99:443` (reverse shell /
  beacon — same IOC as the quarantine sample, so the fleet hunt demo lights up
  across two datasets).

Tests:
- Add `(normalize_network, "network.raw.json", benign=[0,1,2], malicious=[3,4])`
  to `tests/detect/test_benign_and_mitre.py::CASES` — the hard FP gate
  (`test_benign_rows_fire_nothing`) then guards every network rule automatically.
- `tests/normalize/test_network.py` — field mapping, direction derivation
  (LISTEN→ingress, loopback→internal, remote→egress), provenance = collection.
- Extend `test_es_detector_parity.py` coverage (rules auto-included) — confirm
  0-divergence for the new rules on live ES.
- Add a network row to the sample case (`samples/mac-victim/`) so `raptorscope
  demo`, the SPA, and the CI screenshots show the new dataset end-to-end.

## 7. Sequencing / effort

1. `normalize/network.py` + `_NORMALIZERS` + ES template + fixtures + `test_network`.
2. Rules 1–2 (`process.name` + state only) + CASES entry + parity.
3. `_INDICATOR_FIELDS` += destination.address; SPA overview tile; sample-case row.
4. Netstat VQL exe-enrichment → rules 3–4.

Steps 1–3 are a self-contained, shippable increment (dataset + two high-signal
rules + hunt payoff). Step 4 is a follow-on once the enrichment VQL is authored.

## 8. Non-goals / risks

- **No packet capture / flow logs** — point-in-time socket table only; a snapshot
  misses short-lived connections (documented limitation, same class as the
  autoruns mtime caveat).
- **Reverse-shell egress (rule 2) FP** — a developer running `python` that connects
  out will trip it; keep the process list tight, mark experimental, and lean on the
  staging-path variant (rule 3) for higher precision once enrichment lands.
- **netstat process attribution** on macOS can be partial without root; note it and
  prefer the enriched (lsof) feed for `process.executable`.
