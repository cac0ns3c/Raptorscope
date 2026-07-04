// SPDX-License-Identifier: GPL-3.0-or-later
import { useState } from "react";

import type { Alert } from "../api/types";

export type TriageStatus = "ack" | "dismissed";
export interface TriageEntry {
  status?: TriageStatus;
  note?: string;
}

const KEY = "rs_triage";

export function triageKey(caseName: string, a: Alert): string {
  return `${caseName}|${a.rule_id}|${a.doc_id}`;
}

// Use window.localStorage explicitly — under some test runtimes a bare
// `localStorage` global resolves to an unrelated (undefined) binding.
function store(): Storage | null {
  try {
    return window.localStorage;
  } catch {
    return null;
  }
}

function read(): Record<string, TriageEntry> {
  try {
    return JSON.parse(store()?.getItem(KEY) ?? "{}");
  } catch {
    return {};
  }
}

/** Analyst triage state (acknowledge / dismiss / note), persisted locally so it
 *  survives reloads without a server round-trip. */
export function useTriage() {
  const [map, setMap] = useState<Record<string, TriageEntry>>(read);

  function update(key: string, patch: Partial<TriageEntry>) {
    setMap((prev) => {
      const merged = { ...prev[key], ...patch };
      // Drop empty entries so the store stays tidy.
      const next = { ...prev };
      if (!merged.status && !merged.note) delete next[key];
      else next[key] = merged;
      try {
        store()?.setItem(KEY, JSON.stringify(next));
      } catch {
        /* ignore storage failures */
      }
      return next;
    });
  }

  return { map, update };
}
