// SPDX-License-Identifier: GPL-3.0-or-later
import type {
  AIStatus,
  Alert,
  ArtifactPage,
  Case,
  CopilotEvent,
  CopilotResult,
  HuntResult,
  DocContent,
  DocMeta,
  IocResult,
  Overview,
  SearchQuery,
  SearchResult,
  TimelineRow,
} from "./types";

/** A mutable token holder so the client picks up a token set after construction. */
export interface TokenRef {
  current: string | null;
}

/** The SPA's sole data source. Implemented by `createHttpClient` (prod) and by
 *  the fake client used in tests. */
export interface ApiClient {
  listCases(): Promise<Case[]>;
  getOverview(caseName: string): Promise<Overview>;
  getArtifacts(
    caseName: string,
    dataset: string,
    opts?: { limit?: number; offset?: number },
  ): Promise<ArtifactPage>;
  getTimeline(caseName: string, limit?: number): Promise<TimelineRow[]>;
  getAlerts(caseName: string): Promise<Alert[]>;
  search(caseName: string, query: SearchQuery): Promise<SearchResult>;
  login(username: string, password: string): Promise<{ token: string }>;
  listDocs(): Promise<DocMeta[]>;
  getDoc(id: string): Promise<DocContent>;
  hunt(value: string, limit?: number): Promise<HuntResult>;
  aiStatus(): Promise<AIStatus>;
  aiTriage(
    caseName: string,
    ruleId: string,
    docId: string,
  ): Promise<{ analysis: string }>;
  aiSummary(caseName: string): Promise<{ summary: string }>;
  /** Stream the case summary incrementally; resolves when complete. */
  aiSummaryStream(
    caseName: string,
    onChunk: (text: string) => void,
  ): Promise<void>;
  aiIocs(caseName: string): Promise<IocResult>;
  aiNlQuery(caseName: string, question: string): Promise<{ query: SearchQuery }>;
  aiCopilot(caseName: string, question: string): Promise<CopilotResult>;
  /** Stream copilot events (tool calls, then the verdict text). */
  aiCopilotStream(
    caseName: string,
    question: string,
    onEvent: (e: CopilotEvent) => void,
  ): Promise<void>;
}

/** Raised on a 401 so the UI can show the login screen. */
export class AuthError extends Error {}

export function createHttpClient(
  baseUrl: string,
  tokenRef?: TokenRef,
): ApiClient {
  const base = baseUrl.replace(/\/$/, "");
  const c = (name: string) => encodeURIComponent(name);

  async function req<T>(path: string, init?: RequestInit): Promise<T> {
    const headers = new Headers(init?.headers);
    const token = tokenRef?.current;
    if (token) headers.set("Authorization", `Bearer ${token}`);
    const resp = await fetch(`${base}${path}`, { ...init, headers });
    if (resp.status === 401) throw new AuthError("unauthorized");
    if (!resp.ok) throw new Error(`request failed: ${resp.status} ${path}`);
    return (await resp.json()) as T;
  }

  // POST an SSE stream; invoke onPayload for each `data:` JSON, resolve on done.
  async function streamSse(
    path: string,
    onPayload: (p: Record<string, unknown>) => void,
    body?: unknown,
  ): Promise<void> {
    const headers = new Headers({ "Content-Type": "application/json" });
    const token = tokenRef?.current;
    if (token) headers.set("Authorization", `Bearer ${token}`);
    const resp = await fetch(`${base}${path}`, {
      method: "POST",
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });
    if (resp.status === 401) throw new AuthError("unauthorized");
    if (!resp.ok || !resp.body) throw new Error(`stream failed: ${resp.status}`);
    const reader = resp.body.getReader();
    const dec = new TextDecoder();
    let buf = "";
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += dec.decode(value, { stream: true });
      const blocks = buf.split("\n\n");
      buf = blocks.pop() ?? "";
      for (const block of blocks) {
        const line = block.trim();
        if (!line.startsWith("data:")) continue;
        const payload = JSON.parse(line.slice(5).trim());
        if (payload.error) throw new Error("stream error");
        if (payload.done) return;
        onPayload(payload);
      }
    }
  }

  return {
    listCases: () => req(`/cases`),
    getOverview: (name) => req(`/cases/${c(name)}/overview`),
    getArtifacts: (name, dataset, opts = {}) => {
      const params = new URLSearchParams();
      if (opts.limit != null) params.set("limit", String(opts.limit));
      if (opts.offset != null) params.set("offset", String(opts.offset));
      const qs = params.toString();
      return req(
        `/cases/${c(name)}/artifacts/${c(dataset)}${qs ? `?${qs}` : ""}`,
      );
    },
    getTimeline: (name, limit) =>
      req(
        `/cases/${c(name)}/timeline${limit != null ? `?limit=${limit}` : ""}`,
      ),
    getAlerts: (name) => req(`/cases/${c(name)}/alerts`),
    search: (name, query) => {
      const params = new URLSearchParams();
      for (const [k, v] of Object.entries(query)) {
        if (v != null && v !== "") params.set(k, String(v));
      }
      const qs = params.toString();
      return req(`/cases/${c(name)}/search${qs ? `?${qs}` : ""}`);
    },
    login: (username, password) =>
      req(`/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      }),
    listDocs: () => req(`/docs`),
    getDoc: (id) => req(`/docs/${c(id)}`),
    hunt: (value, limit = 200) =>
      req(`/hunt?q=${encodeURIComponent(value)}&limit=${limit}`),
    aiStatus: () => req(`/ai/status`),
    aiTriage: (name, ruleId, docId) =>
      req(`/cases/${c(name)}/ai/triage`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rule_id: ruleId, doc_id: docId }),
      }),
    aiSummary: (name) =>
      req(`/cases/${c(name)}/ai/summary`, { method: "POST" }),
    aiSummaryStream: (name, onChunk) =>
      streamSse(`/cases/${c(name)}/ai/summary/stream`, (p) => {
        if (p.text) onChunk(p.text as string);
      }),
    aiCopilotStream: (name, question, onEvent) =>
      streamSse(
        `/cases/${c(name)}/ai/copilot/stream`,
        (p) => onEvent(p as unknown as CopilotEvent),
        { question },
      ),
    aiIocs: (name) => req(`/cases/${c(name)}/ai/iocs`, { method: "POST" }),
    aiNlQuery: (name, question) =>
      req(`/cases/${c(name)}/ai/nl-query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      }),
    aiCopilot: (name, question) =>
      req(`/cases/${c(name)}/ai/copilot`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      }),
  };
}
