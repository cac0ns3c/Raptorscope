// SPDX-License-Identifier: GPL-3.0-or-later
import type {
  Alert,
  ArtifactPage,
  Case,
  Overview,
  SearchQuery,
  SearchResult,
  TimelineRow,
} from "./types";

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
}

async function getJson<T>(url: string): Promise<T> {
  const resp = await fetch(url);
  if (!resp.ok) {
    throw new Error(`request failed: ${resp.status} ${url}`);
  }
  return (await resp.json()) as T;
}

export function createHttpClient(baseUrl: string): ApiClient {
  const base = baseUrl.replace(/\/$/, "");
  const c = (name: string) => encodeURIComponent(name);
  return {
    listCases: () => getJson(`${base}/cases`),
    getOverview: (name) => getJson(`${base}/cases/${c(name)}/overview`),
    getArtifacts: (name, dataset, opts = {}) => {
      const params = new URLSearchParams();
      if (opts.limit != null) params.set("limit", String(opts.limit));
      if (opts.offset != null) params.set("offset", String(opts.offset));
      const qs = params.toString();
      return getJson(
        `${base}/cases/${c(name)}/artifacts/${c(dataset)}${qs ? `?${qs}` : ""}`,
      );
    },
    getTimeline: (name, limit) =>
      getJson(
        `${base}/cases/${c(name)}/timeline${limit != null ? `?limit=${limit}` : ""}`,
      ),
    getAlerts: (name) => getJson(`${base}/cases/${c(name)}/alerts`),
    search: (name, query) => {
      const params = new URLSearchParams();
      for (const [k, v] of Object.entries(query)) {
        if (v != null && v !== "") params.set(k, String(v));
      }
      const qs = params.toString();
      return getJson(`${base}/cases/${c(name)}/search${qs ? `?${qs}` : ""}`);
    },
  };
}
