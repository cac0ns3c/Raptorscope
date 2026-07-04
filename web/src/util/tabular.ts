// SPDX-License-Identifier: GPL-3.0-or-later
import type { Doc } from "../api/types";
import { cell, dig } from "./dig";

/** Flatten a nested doc into sorted [dotted-path, value] pairs (skips `_id`). */
export function flatten(doc: Doc): [string, unknown][] {
  const out: [string, unknown][] = [];
  const walk = (v: unknown, prefix: string) => {
    if (v && typeof v === "object" && !Array.isArray(v)) {
      for (const [k, val] of Object.entries(v)) {
        walk(val, prefix ? `${prefix}.${k}` : k);
      }
    } else {
      out.push([prefix, v]);
    }
  };
  walk(doc, "");
  return out.filter(([k]) => k !== "_id").sort((a, b) => a[0].localeCompare(b[0]));
}

function csvEscape(value: unknown): string {
  const s = value == null ? "" : String(value);
  return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}

/** Build CSV text for `items` using the given columns (header + dotted path). */
export function buildCsv(
  items: Doc[],
  columns: { header: string; path: string }[],
): string {
  const head = columns.map((c) => csvEscape(c.header)).join(",");
  const rows = items.map((d) =>
    columns.map((c) => csvEscape(cell(dig(d, c.path)))).join(","),
  );
  return [head, ...rows].join("\n");
}

/** Trigger a client-side file download (no-op if DOM APIs are unavailable). */
export function download(filename: string, content: string, mime: string): void {
  try {
    const blob = new Blob([content], { type: mime });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  } catch {
    /* ignore in non-DOM contexts */
  }
}
