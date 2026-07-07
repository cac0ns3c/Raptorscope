// SPDX-License-Identifier: GPL-3.0-or-later

/** Format an integer with locale thousands separators (e.g. 28431 -> "28,431"). */
export function fmtNum(n: number): string {
  return n.toLocaleString();
}

/** Human-readable UTC time, sub-second precision dropped:
 *  "2026-07-07T07:46:10.037835264Z" -> "2026-07-07 07:46:10". Falls back to the
 *  raw value when it isn't an ISO-ish timestamp. */
export function fmtTime(iso: string | number | null | undefined): string {
  if (iso == null || iso === "") return "";
  const m = /^(\d{4}-\d{2}-\d{2})[T ](\d{2}:\d{2}:\d{2})/.exec(String(iso));
  return m ? `${m[1]} ${m[2]}` : String(iso);
}
