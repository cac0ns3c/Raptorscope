// SPDX-License-Identifier: GPL-3.0-or-later

/** Read a dotted path out of a nested object; undefined if any hop is missing. */
export function dig(doc: unknown, path: string): unknown {
  let cur: unknown = doc;
  for (const key of path.split(".")) {
    if (cur == null || typeof cur !== "object") return undefined;
    cur = (cur as Record<string, unknown>)[key];
  }
  return cur;
}

/** Render a cell value as a string for display. */
export function cell(value: unknown): string {
  if (value == null) return "—";
  if (typeof value === "boolean") return value ? "yes" : "no";
  return String(value);
}
