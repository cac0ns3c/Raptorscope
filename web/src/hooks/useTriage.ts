// SPDX-License-Identifier: GPL-3.0-or-later
import { useEffect, useState } from "react";

import type { Alert } from "../api/types";
import { useApi } from "../context/ApiContext";

export type TriageStatus = "ack" | "dismissed";
export interface TriageEntry {
  status?: TriageStatus;
  note?: string;
  actor?: string;
  ts?: string;
}

export function triageKey(caseName: string, a: Alert): string {
  return `${caseName}|${a.rule_id}|${a.doc_id}`;
}

const lkey = (c: string) => `rs_triage:${c}`;

function readLocal(caseName: string): Record<string, TriageEntry> {
  try {
    return JSON.parse(window.localStorage.getItem(lkey(caseName)) ?? "{}");
  } catch {
    return {};
  }
}

function writeLocal(caseName: string, map: Record<string, TriageEntry>): void {
  try {
    window.localStorage.setItem(lkey(caseName), JSON.stringify(map));
  } catch {
    /* ignore storage failures */
  }
}

/** Analyst triage state (ack / dismiss / note). The server is the system of
 *  record (shared across analysts, audited with actor+ts); localStorage is only
 *  an offline cache for instant paint and offline resilience. */
export function useTriage(caseName: string) {
  const api = useApi();
  const [map, setMap] = useState<Record<string, TriageEntry>>(() =>
    readLocal(caseName),
  );

  useEffect(() => {
    let live = true;
    setMap(readLocal(caseName)); // instant from cache
    api
      .getTriage(caseName)
      .then((server) => {
        if (!live) return;
        const m: Record<string, TriageEntry> = {};
        for (const [k, v] of Object.entries(server)) {
          m[`${caseName}|${k}`] = v as TriageEntry;
        }
        setMap(m);
        writeLocal(caseName, m);
      })
      .catch(() => {
        /* offline / no endpoint: keep the local cache */
      });
    return () => {
      live = false;
    };
  }, [api, caseName]);

  function update(key: string, patch: Partial<TriageEntry>) {
    setMap((prev) => {
      const merged = { ...prev[key], ...patch };
      const next = { ...prev };
      if (!merged.status && !merged.note) delete next[key];
      else next[key] = merged;
      writeLocal(caseName, next);
      return next;
    });
    // key === `${caseName}|${rule_id}|${doc_id}`
    const rest = key.slice(caseName.length + 1);
    const sep = rest.indexOf("|");
    const ruleId = rest.slice(0, sep);
    const docId = rest.slice(sep + 1);
    const serverPatch: { status?: string | null; note?: string | null } = {};
    if ("status" in patch) serverPatch.status = patch.status ?? null;
    if ("note" in patch) serverPatch.note = patch.note ?? null;
    api.setTriage(caseName, ruleId, docId, serverPatch).catch(() => {
      /* offline: local cache already reflects the change */
    });
  }

  return { map, update };
}
