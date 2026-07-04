// SPDX-License-Identifier: GPL-3.0-or-later
// Optional Kibana integration. Set VITE_KIBANA_URL (e.g. http://localhost:5601)
// to surface an "Open in Kibana" link that deep-links Discover to the case host.

export function kibanaBase(): string {
  return (import.meta.env.VITE_KIBANA_URL ?? "").replace(/\/$/, "");
}

/** A Discover deep link scoped (via KQL) to one case's host. */
export function kibanaDiscoverUrl(base: string, caseName: string): string {
  const kql = `host.name:"${caseName}"`;
  return `${base}/app/discover#/?_a=(query:(language:kuery,query:'${encodeURIComponent(
    kql,
  )}'))`;
}
