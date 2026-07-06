// SPDX-License-Identifier: GPL-3.0-or-later

/** Format an integer with locale thousands separators (e.g. 28431 -> "28,431"). */
export function fmtNum(n: number): string {
  return n.toLocaleString();
}
