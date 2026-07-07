// SPDX-License-Identifier: GPL-3.0-or-later
// Mirrors the Phase-3 backend JSON contracts (raptorscope.api).

export interface Case {
  name: string;
  doc_count: number;
  datasets: string[];
}

export interface Overview {
  case: string;
  total: number;
  datasets: Record<string, number>;
  persistence_types: Record<string, number>;
  unsigned: { process: number; inventory: number };
}

/** An ECS document as returned by the store (source fields + injected `_id`). */
export type Doc = Record<string, unknown> & { _id: string };

export interface ArtifactPage {
  dataset: string;
  total: number;
  items: Doc[];
}

export interface SearchQuery {
  q?: string;
  dataset?: string;
  field?: string;
  op?: string;
  value?: string;
  limit?: number;
}

export interface SearchResult {
  total: number;
  items: Doc[];
}

export interface TimelineRowExtra {
  /** "mtime" when the timestamp is a file-modification time, not a true event time. */
  time_source?: string | null;
}

export interface TimelineRow extends TimelineRowExtra {
  timestamp: string;
  dataset: string;
  category: string[] | null;
  summary: string;
  doc_id: string;
}

export interface DocMeta {
  id: string;
  title: string;
}

export interface DocContent {
  id: string;
  title: string;
  markdown: string;
}

export interface IOC {
  type: string;
  value: string;
  context: string;
}

export interface IocResult {
  iocs: IOC[];
}

export interface HuntHost {
  host: string;
  count: number;
  datasets: string[];
  samples: { dataset: string | null; summary: string; doc_id: string }[];
}

export interface HuntResult {
  value: string;
  total: number;
  host_count: number;
  hosts: HuntHost[];
}

export interface AIStatus {
  enabled: boolean;
  model: string | null;
}

export interface Citation {
  tool: string;
  input: Record<string, unknown>;
}

export interface CopilotResult {
  answer: string;
  citations: Citation[];
}

export type CopilotEvent =
  | { type: "tool"; tool: string; input: Record<string, unknown> }
  | { type: "text"; text: string };

export interface Alert {
  rule_id: string;
  title: string;
  level: string;
  dataset: string;
  doc_id: string;
  evidence: Record<string, unknown>;
  // detection metadata (surfaced from the rule)
  mitre?: string[];
  description?: string;
  falsepositives?: string[];
  status?: string;
  time_source?: string | null;
}
