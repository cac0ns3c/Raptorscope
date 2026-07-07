// SPDX-License-Identifier: GPL-3.0-or-later
import { useEffect, useMemo, useRef, useState } from "react";

import type { Doc } from "../api/types";
import { useApi } from "../context/ApiContext";
import { useAsync } from "../hooks/useAsync";
import { useColumns } from "../hooks/useColumns";
import { State } from "../ui/State";
import { rowActivation } from "../util/a11y";
import { cell, dig } from "../util/dig";
import { fmtTime } from "../util/format";
import { buildCsv, download } from "../util/tabular";
import { ColumnPicker } from "./ColumnPicker";
import { columnsFor } from "./columns";
import { DetailDrawer } from "./DetailDrawer";

const MONO = new Set(["file.path", "process.executable"]);

function compare(a: unknown, b: unknown): number {
  if (typeof a === "number" && typeof b === "number") return a - b;
  return String(a ?? "").localeCompare(String(b ?? ""));
}

export function ArtifactTable({
  caseName,
  dataset,
  pageSize = 50,
  highlightId,
}: {
  caseName: string;
  dataset: string;
  pageSize?: number;
  highlightId?: string;
}) {
  const api = useApi();
  const [offset, setOffset] = useState(0);
  const [sort, setSort] = useState<{ path: string; dir: 1 | -1 } | null>(null);
  const [selected, setSelected] = useState<Doc | null>(null);
  const handledHighlight = useRef<string | undefined>(undefined);

  // Reset paging/sort when the case or dataset changes.
  useEffect(() => {
    setOffset(0);
    setSort(null);
    handledHighlight.current = undefined;
  }, [caseName, dataset]);

  const { data, loading, error, reload } = useAsync(
    () => api.getArtifacts(caseName, dataset, { limit: 100000 }),
    [caseName, dataset],
  );

  const {
    columns: chosen,
    available,
    visible,
    toggle,
    reset,
  } = useColumns(dataset, data?.items ?? []);
  // Never render a column-less table — fall back to the dataset defaults if the
  // user has hidden everything.
  const columns = chosen.length ? chosen : columnsFor(dataset);

  const sorted = useMemo(() => {
    const items = data?.items ?? [];
    if (!sort) return items;
    return [...items].sort(
      (a, b) => compare(dig(a, sort.path), dig(b, sort.path)) * sort.dir,
    );
  }, [data, sort]);

  // Pivot target: jump to the highlighted doc's page and open its drawer (once
  // per new highlight) so alert→evidence lands ON the document, not near it.
  useEffect(() => {
    if (!highlightId || !data) return;
    if (handledHighlight.current === highlightId) return;
    const idx = sorted.findIndex((d) => d._id === highlightId);
    if (idx >= 0) {
      handledHighlight.current = highlightId;
      setOffset(Math.floor(idx / pageSize) * pageSize);
      setSelected(sorted[idx]);
    }
  }, [highlightId, data, sorted, pageSize]);

  const shortDs = dataset.replace("macos.", "");
  if (loading) return <State variant="loading" message={`Loading ${shortDs}…`} />;
  if (error || !data)
    return (
      <State variant="error" message={`Failed to load ${shortDs}.`} onRetry={reload} />
    );
  if (data.total === 0)
    return <State variant="empty" message={`No ${shortDs} events.`} />;

  const from = offset + 1;
  const to = Math.min(offset + pageSize, data.total);
  const pageItems = sorted.slice(offset, offset + pageSize);

  function toggleSort(path: string) {
    setOffset(0);
    setSort((s) =>
      s && s.path === path ? { path, dir: (s.dir * -1) as 1 | -1 } : { path, dir: 1 },
    );
  }

  return (
    <section className="artifact-view" aria-label={`artifacts ${dataset}`}>
      <div className="view-toolbar">
        <span className="muted">{data.total} rows</span>
        <span className="view-export">
          <ColumnPicker
            available={available}
            visible={visible}
            toggle={toggle}
            reset={reset}
          />
          <button
            onClick={() =>
              download(
                `${dataset}.csv`,
                buildCsv(sorted, columns),
                "text/csv",
              )
            }
          >
            CSV
          </button>
          <button
            onClick={() =>
              download(
                `${dataset}.json`,
                JSON.stringify(sorted, null, 2),
                "application/json",
              )
            }
          >
            JSON
          </button>
        </span>
      </div>
      <div className="table-scroll">
        <table className="grid">
          <thead>
            <tr>
              {columns.map((col) => (
                <th
                  key={col.path}
                  className="sortable"
                  tabIndex={0}
                  aria-sort={
                    sort?.path === col.path
                      ? sort.dir === 1
                        ? "ascending"
                        : "descending"
                      : undefined
                  }
                  onClick={() => toggleSort(col.path)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      toggleSort(col.path);
                    }
                  }}
                >
                  {col.header}
                  {sort?.path === col.path && (
                    <span className="sort-caret">
                      {sort.dir === 1 ? " ▲" : " ▼"}
                    </span>
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {pageItems.map((doc) => (
              <tr
                key={doc._id}
                data-testid="artifact-row"
                className={`clickable ${doc._id === highlightId ? "highlight" : ""}`}
                aria-label="open document detail"
                {...rowActivation(() => setSelected(doc))}
              >
                {columns.map((col) => {
                  const value = dig(doc, col.path);
                  if (typeof value === "boolean") {
                    return (
                      <td key={col.path}>
                        <span className={`pill ${value ? "pill-yes" : "pill-no"}`}>
                          {value ? "yes" : "no"}
                        </span>
                      </td>
                    );
                  }
                  const text =
                    col.path === "@timestamp"
                      ? fmtTime(value as string)
                      : cell(value);
                  return (
                    <td
                      key={col.path}
                      className={MONO.has(col.path) ? "mono" : undefined}
                      title={col.path === "@timestamp" ? String(value) : text || undefined}
                    >
                      {text}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="pager">
        <button
          onClick={() => setOffset(Math.max(0, offset - pageSize))}
          disabled={offset === 0}
        >
          Prev
        </button>
        <span className="range">
          {from}–{to} of {data.total}
        </span>
        <button
          onClick={() => setOffset(offset + pageSize)}
          disabled={to >= data.total}
        >
          Next
        </button>
      </div>

      {selected && (
        <DetailDrawer doc={selected} onClose={() => setSelected(null)} />
      )}
    </section>
  );
}
