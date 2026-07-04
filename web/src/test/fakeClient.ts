// SPDX-License-Identifier: GPL-3.0-or-later
// An in-memory ApiClient seeded to mirror the Phase-3 backend seed (a dirty
// case `mac-victim` and a benign `mac-clean`). Shared by all component tests.
import type { ApiClient } from "../api/client";
import type {
  Alert,
  ArtifactPage,
  Case,
  Doc,
  Overview,
  TimelineRow,
} from "../api/types";

export const DIRTY = "mac-victim";
export const CLEAN = "mac-clean";

function persistenceDoc(
  id: string,
  type: string,
  label: string,
  path: string,
): Doc {
  return {
    _id: id,
    "@timestamp": "2025-01-01T00:00:00Z",
    event: { dataset: "macos.persistence" },
    file: { path, name: path.split("/").pop() },
    process: { executable: path },
    raptorscope: { persistence: { type, label } },
  };
}

const persistence: Doc[] = [
  persistenceDoc("p0", "launch_daemon", "com.apple.softwareupdated", "/Library/LaunchDaemons/com.apple.softwareupdated.plist"),
  persistenceDoc("p1", "launch_agent", "com.google.keystone.agent", "/Library/LaunchAgents/com.google.keystone.agent.plist"),
  persistenceDoc("p2", "launch_agent", "com.apple.updates", "/Users/analyst/Library/LaunchAgents/com.apple.updates.plist"),
  persistenceDoc("p3", "launch_daemon", "com.system.helper", "/Users/Shared/.cache/com.system.helper.plist"),
  persistenceDoc("p4", "login_item", "Dropbox", "/Applications/Dropbox.app"),
  persistenceDoc("p5", "login_item", "SystemUpdater", "/Users/Shared/.updater/SystemUpdater.app"),
  persistenceDoc("p6", "cron", "/etc/crontab", "/etc/crontab"),
  persistenceDoc("p7", "cron", "/usr/lib/cron/tabs/analyst", "/usr/lib/cron/tabs/analyst"),
  persistenceDoc("p8", "config_profile", "com.apple.mdm.corp.wifi", "/var/db/ConfigurationProfiles/Store/com.apple.mdm.corp.wifi.plist"),
  persistenceDoc("p9", "config_profile", "com.systemhelper.support", "/var/db/ConfigurationProfiles/Store/com.systemhelper.support.plist"),
  persistenceDoc("p10", "btm", "com.docker.helper", "/Applications/Docker.app/Contents/MacOS/com.docker.helper"),
  persistenceDoc("p11", "btm", "com.apple.helperd", "/private/tmp/.x/helperd"),
];

const process: Doc[] = [
  { _id: "proc0", "@timestamp": "2026-07-03T08:00:00Z", event: { dataset: "macos.process" }, process: { name: "launchd", pid: 1, executable: "/sbin/launchd", code_signature: { trusted: true } }, user: { name: "root" } },
  { _id: "proc1", "@timestamp": "2026-07-03T09:12:44Z", event: { dataset: "macos.process" }, process: { name: "Safari", pid: 842, executable: "/Applications/Safari.app/Contents/MacOS/Safari", code_signature: { trusted: true } }, user: { name: "analyst" } },
  { _id: "proc2", "@timestamp": "2026-07-03T09:41:03Z", event: { dataset: "macos.process" }, process: { name: "helper", pid: 5099, executable: "/private/tmp/.cache/helper", code_signature: { trusted: false } }, user: { name: "analyst" } },
];

const quarantine: Doc[] = [
  { _id: "q0", "@timestamp": "2025-05-04T16:20:11Z", event: { dataset: "macos.quarantine" }, file: { path: "/Users/analyst/Downloads/Firefox.dmg", name: "Firefox.dmg" }, url: { original: "https://www.mozilla.org/firefox/download/" }, process: { name: "Safari" } },
  { _id: "q1", "@timestamp": "2026-07-02T21:03:55Z", event: { dataset: "macos.quarantine" }, file: { path: "/Users/analyst/Downloads/Invoice.pdf.command", name: "Invoice.pdf.command" }, url: { original: "http://45.9.148.99/promo" }, process: { name: "Google Chrome" } },
];

const tcc: Doc[] = [
  { _id: "tcc0", "@timestamp": "2025-01-05T12:00:00Z", event: { dataset: "macos.tcc" }, raptorscope: { tcc: { service: "kTCCServiceSystemPolicyAllFiles", client: "com.apple.Terminal", allowed: true } } },
  { _id: "tcc1", "@timestamp": "2025-03-11T08:30:00Z", event: { dataset: "macos.tcc" }, raptorscope: { tcc: { service: "kTCCServiceCamera", client: "us.zoom.xos", allowed: true } } },
  { _id: "tcc2", "@timestamp": "2026-07-02T22:14:38Z", event: { dataset: "macos.tcc" }, raptorscope: { tcc: { service: "kTCCServiceAccessibility", client: "/Users/Shared/.helper/agent", allowed: true } } },
];

const inventory: Doc[] = [
  { _id: "inv0", "@timestamp": "2025-04-02T07:45:00Z", event: { dataset: "macos.inventory" }, file: { path: "/Applications/Slack.app", name: "Slack.app" }, raptorscope: { app: { name: "Slack", version: "4.36.140", signed: true } } },
  { _id: "inv1", "@timestamp": "2026-07-01T05:12:20Z", event: { dataset: "macos.inventory" }, file: { path: "/Users/analyst/.local/Updater.app", name: "Updater.app" }, raptorscope: { app: { name: "Updater", version: "1.0", signed: false } } },
];

const DIRTY_DOCS: Record<string, Doc[]> = {
  "macos.persistence": persistence,
  "macos.process": process,
  "macos.quarantine": quarantine,
  "macos.tcc": tcc,
  "macos.inventory": inventory,
};

const CLEAN_DOCS: Record<string, Doc[]> = {
  "macos.persistence": persistence.slice(0, 2),
  "macos.process": process.slice(0, 2),
};

const OVERVIEW: Overview = {
  case: DIRTY,
  total: 22,
  datasets: {
    "macos.persistence": 12,
    "macos.process": 3,
    "macos.quarantine": 2,
    "macos.tcc": 3,
    "macos.inventory": 2,
  },
  persistence_types: {
    launch_agent: 2,
    launch_daemon: 2,
    login_item: 2,
    cron: 2,
    config_profile: 2,
    btm: 2,
  },
  unsigned: { process: 1, inventory: 1 },
};

const ALERTS: Alert[] = [
  { rule_id: "r-persist", title: "macOS persistence program in suspicious path", level: "high", dataset: "macos.persistence", doc_id: "p3", evidence: { "file.path": "/Users/Shared/.cache/com.system.helper.plist" } },
  { rule_id: "r-proc", title: "macOS process running from a suspicious path", level: "high", dataset: "macos.process", doc_id: "proc2", evidence: { "process.executable": "/private/tmp/.cache/helper" } },
  { rule_id: "r-tcc", title: "macOS sensitive TCC grant to a non-Apple client", level: "high", dataset: "macos.tcc", doc_id: "tcc2", evidence: { "raptorscope.tcc.client": "/Users/Shared/.helper/agent" } },
  { rule_id: "r-quar", title: "macOS quarantined executable or script downloaded", level: "medium", dataset: "macos.quarantine", doc_id: "q1", evidence: { "file.name": "Invoice.pdf.command" } },
  { rule_id: "r-inv", title: "macOS unsigned application installed outside /Applications", level: "medium", dataset: "macos.inventory", doc_id: "inv1", evidence: { "file.path": "/Users/analyst/.local/Updater.app" } },
];

function timelineFor(docs: Record<string, Doc[]>): TimelineRow[] {
  const rows: TimelineRow[] = [];
  for (const list of Object.values(docs)) {
    for (const d of list) {
      const dataset = (d.event as { dataset: string }).dataset;
      rows.push({
        timestamp: (d["@timestamp"] as string) ?? "",
        dataset,
        category: null,
        summary: `${dataset} ${d._id}`,
        doc_id: d._id,
        // persistence artifacts are dated by file mtime
        time_source: dataset === "macos.persistence" ? "mtime" : null,
      });
    }
  }
  rows.sort((a, b) => (a.timestamp < b.timestamp ? 1 : -1));
  return rows;
}

const CASES: Case[] = [
  { name: DIRTY, doc_count: 22, datasets: Object.keys(DIRTY_DOCS).sort() },
  { name: CLEAN, doc_count: 4, datasets: Object.keys(CLEAN_DOCS).sort() },
];

export function makeFakeClient(): ApiClient {
  const docsFor = (name: string) => (name === DIRTY ? DIRTY_DOCS : CLEAN_DOCS);

  return {
    listCases: async () => CASES,
    getOverview: async (name) => ({ ...OVERVIEW, case: name }),
    getArtifacts: async (name, dataset, opts = {}): Promise<ArtifactPage> => {
      const all = docsFor(name)[dataset] ?? [];
      const offset = opts.offset ?? 0;
      const limit = opts.limit ?? 50;
      return { dataset, total: all.length, items: all.slice(offset, offset + limit) };
    },
    getTimeline: async (name, limit) => {
      const rows = timelineFor(docsFor(name));
      return limit != null ? rows.slice(0, limit) : rows;
    },
    getAlerts: async (name) => (name === DIRTY ? ALERTS : []),
    search: async (name, query) => {
      let items = Object.entries(docsFor(name))
        .filter(([ds]) => !query.dataset || ds === query.dataset)
        .flatMap(([, list]) => list);
      const q = (query.q ?? "").trim().toLowerCase();
      if (q) {
        items = items.filter((d) => JSON.stringify(d).toLowerCase().includes(q));
      }
      if (query.field && query.value != null && query.value !== "") {
        items = items.filter((d) => {
          const cur = query.field!
            .split(".")
            .reduce<unknown>(
              (o, k) =>
                o && typeof o === "object"
                  ? (o as Record<string, unknown>)[k]
                  : undefined,
              d,
            );
          return String(cur ?? "")
            .toLowerCase()
            .includes(String(query.value).toLowerCase());
        });
      }
      return { total: items.length, items: items.slice(0, query.limit ?? 100) };
    },
    login: async (username, password) => {
      if (username === "analyst" && password === "s3cret") {
        return { token: "fake-token" };
      }
      throw new Error("request failed: 401 /login");
    },
    listDocs: async () => [
      { id: "readme", title: "Overview" },
      { id: "kibana", title: "Using Kibana" },
    ],
    getDoc: async (id) => ({
      id,
      title: id === "kibana" ? "Using Kibana" : "Overview",
      markdown: `# ${id}\n\nSample documentation body for **${id}**.`,
    }),
    hunt: async (value) => {
      const shared = /45\.9|tmp|helper/i.test(value);
      const hosts = shared
        ? [
            { host: DIRTY, count: 3, datasets: ["macos.process", "macos.persistence"], samples: [{ dataset: "macos.process", summary: `${value} beacon`, doc_id: "1" }] },
            { host: CLEAN, count: 1, datasets: ["macos.process"], samples: [{ dataset: "macos.process", summary: `${value}`, doc_id: "2" }] },
          ]
        : [];
      return {
        value,
        total: hosts.reduce((s, h) => s + h.count, 0),
        host_count: hosts.length,
        hosts,
      };
    },
    aiStatus: async () => ({ enabled: true, model: "claude-opus-4-8" }),
    aiTriage: async (_name, ruleId) => ({
      analysis: `**Assessment** — ${ruleId} is likely malicious.`,
    }),
    aiSummary: async () => ({
      summary: "**Bottom line** — one host shows staged persistence and a beacon.",
    }),
    aiSummaryStream: async (_name, onChunk) => {
      for (const chunk of ["**Bottom", " line** — ", "staged persistence and a beacon."]) {
        onChunk(chunk);
      }
    },
    aiIocs: async () => ({
      iocs: [
        { type: "ip", value: "45.9.148.99", context: "C2 beacon" },
        { type: "path", value: "/private/tmp/.cache/helper", context: "implant" },
      ],
    }),
    aiNlQuery: async (_name, question) => ({
      query: { q: question.includes("tmp") ? "/private/tmp" : question, dataset: "macos.process" },
    }),
    aiCopilot: async (_name, question) => ({
      answer: `**Verdict** — regarding "${question}": suspicious activity found.`,
      citations: [
        { tool: "get_overview", input: {} },
        { tool: "search_case", input: { q: "/private/tmp" } },
      ],
    }),
    aiCopilotStream: async (_name, _question, onEvent) => {
      onEvent({ type: "tool", tool: "get_overview", input: {} });
      onEvent({ type: "tool", tool: "search_case", input: { q: "/private/tmp" } });
      onEvent({ type: "text", text: "**Verdict** — " });
      onEvent({ type: "text", text: "suspicious activity found." });
    },
  };
}

export const seed = { cases: CASES, OVERVIEW, ALERTS, persistence, process, quarantine, tcc, inventory };
