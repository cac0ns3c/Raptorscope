// SPDX-License-Identifier: GPL-3.0-or-later
import { useEffect, useMemo, useState } from "react";

import type { Doc } from "../api/types";
import type { Column } from "../components/columns";
import { columnsFor } from "../components/columns";
import { flatten } from "../util/tabular";

const lkey = (ds: string) => `rs_cols:${ds}`;

function humanize(path: string): string {
  const last = path.split(".").pop() ?? path;
  return last.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

/** Column visibility for the artifact table. The dataset's curated columns are the
 *  default; any other field present in the data can be added. Choice persists per
 *  dataset in localStorage. */
export function useColumns(dataset: string, docs: Doc[]) {
  // Every column the user could pick: curated first (nice headers), then any other
  // flattened field seen in the data, sorted by path.
  const available = useMemo<Column[]>(() => {
    const curated = columnsFor(dataset);
    const seen = new Set(curated.map((c) => c.path));
    const extra: Column[] = [];
    for (const d of docs.slice(0, 200)) {
      for (const [path] of flatten(d)) {
        if (path === "_id" || seen.has(path)) continue;
        seen.add(path);
        extra.push({ header: humanize(path), path });
      }
    }
    extra.sort((a, b) => a.path.localeCompare(b.path));
    return [...curated, ...extra];
  }, [dataset, docs]);

  const defaults = useMemo(
    () => columnsFor(dataset).map((c) => c.path),
    [dataset],
  );
  const [visible, setVisible] = useState<string[]>(defaults);

  // Load the saved choice when the dataset changes.
  useEffect(() => {
    let stored: string[] | null = null;
    try {
      stored = JSON.parse(window.localStorage.getItem(lkey(dataset)) ?? "null");
    } catch {
      stored = null;
    }
    setVisible(stored && stored.length ? stored : defaults);
  }, [dataset, defaults]);

  function persist(paths: string[]) {
    try {
      window.localStorage.setItem(lkey(dataset), JSON.stringify(paths));
    } catch {
      /* ignore */
    }
  }

  function toggle(path: string) {
    setVisible((prev) => {
      const set = new Set(prev);
      set.has(path) ? set.delete(path) : set.add(path);
      // Keep render order stable: follow `available` order, not click order.
      const ordered = available.map((c) => c.path).filter((p) => set.has(p));
      persist(ordered);
      return ordered;
    });
  }

  function reset() {
    try {
      window.localStorage.removeItem(lkey(dataset));
    } catch {
      /* ignore */
    }
    setVisible(defaults);
  }

  const shown = new Set(visible);
  const columns = useMemo(
    () => available.filter((c) => shown.has(c.path)),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [available, visible],
  );

  return { columns, available, visible: shown, toggle, reset };
}
