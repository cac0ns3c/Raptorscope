// SPDX-License-Identifier: GPL-3.0-or-later
import { useEffect, useState } from "react";

import { useApi } from "../context/ApiContext";
import { useAsync } from "../hooks/useAsync";
import { cell, dig } from "../util/dig";
import { columnsFor } from "./columns";

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

  // Reset paging when the case or dataset changes.
  useEffect(() => setOffset(0), [caseName, dataset]);

  const { data, loading, error } = useAsync(
    () => api.getArtifacts(caseName, dataset, { limit: pageSize, offset }),
    [caseName, dataset, offset, pageSize],
  );

  const columns = columnsFor(dataset);

  if (loading) return <p className="muted">Loading {dataset}…</p>;
  if (error || !data) return <p className="error">Failed to load {dataset}.</p>;
  if (data.total === 0) return <p className="muted">No {dataset} events.</p>;

  const from = offset + 1;
  const to = Math.min(offset + pageSize, data.total);

  return (
    <section className="artifact-view" aria-label={`artifacts ${dataset}`}>
      <table className="grid">
        <thead>
          <tr>
            {columns.map((col) => (
              <th key={col.path}>{col.header}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.items.map((doc) => (
            <tr
              key={doc._id}
              data-testid="artifact-row"
              className={doc._id === highlightId ? "highlight" : undefined}
            >
              {columns.map((col) => (
                <td key={col.path}>{cell(dig(doc, col.path))}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>

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
    </section>
  );
}
