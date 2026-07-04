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

export interface TimelineRow {
  timestamp: string;
  dataset: string;
  category: string[] | null;
  summary: string;
  doc_id: string;
}

export interface Alert {
  rule_id: string;
  title: string;
  level: string;
  dataset: string;
  doc_id: string;
  evidence: Record<string, unknown>;
}
