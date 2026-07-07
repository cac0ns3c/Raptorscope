// SPDX-License-Identifier: GPL-3.0-or-later
import { useState } from "react";

import { useApi } from "../context/ApiContext";
import { useAsync } from "../hooks/useAsync";
import { State } from "../ui/State";
import { rowActivation } from "../util/a11y";
import { fmtTime } from "../util/format";

export function Timeline({
  caseName,
  limit = 200,
  onPivot,
}: {
  caseName: string;
  limit?: number;
  onPivot?: (dataset: string, docId: string) => void;
}) {
  const api = useApi();
  const [filter, setFilter] = useState<string | null>(null);
  const { data, loading, error, reload } = useAsync(
    () => api.getTimeline(caseName, limit),
    [caseName, limit],
  );

  if (loading) return <State variant="loading" message="Loading timeline…" />;
  if (error || !data)
    return (
      <State variant="error" message="Failed to load the timeline." onRetry={reload} />
    );
  if (data.length === 0)
    return <State variant="empty" message="No events in this case." />;

  const datasets = [...new Set(data.map((r) => r.dataset))].sort();
  const rows = filter ? data.filter((r) => r.dataset === filter) : data;

  return (
    <>
      <div className="timeline-filters" aria-label="timeline filters">
        <button
          data-dataset=""
          className={filter === null ? "chip active" : "chip"}
          onClick={() => setFilter(null)}
        >
          all {data.length}
        </button>
        {datasets.map((ds) => (
          <button
            key={ds}
            data-dataset={ds}
            className={filter === ds ? "chip active" : "chip"}
            onClick={() => setFilter((f) => (f === ds ? null : ds))}
          >
            {ds.replace("macos.", "")} {data.filter((r) => r.dataset === ds).length}
          </button>
        ))}
        {data.length >= limit && (
          <span className="timeline-cap" title="Increase the limit to see older events">
            showing newest {limit}
          </span>
        )}
      </div>
      <ol className="timeline" aria-label="timeline">
        {rows.map((row) => (
        <li
          key={row.doc_id}
          className={`timeline-row ${onPivot ? "clickable" : ""}`}
          data-dataset={row.dataset}
          aria-label={onPivot ? "open in artifacts" : undefined}
          {...(onPivot ? rowActivation(() => onPivot(row.dataset, row.doc_id)) : {})}
        >
          <time className="ts" dateTime={row.timestamp} title={row.timestamp}>
            <span data-testid="tl-ts">{fmtTime(row.timestamp)}</span>
            {row.time_source === "mtime" && (
              <span
                className="ts-provenance"
                title="Dated by file modification time (mtime), not a confirmed event time — ordering is approximate."
              >
                mtime
              </span>
            )}
          </time>
          <span className="dot" aria-hidden="true" />
          <span className="tl-main">
            <span className="badge" data-dataset={row.dataset}>
              {row.dataset.replace("macos.", "")}
            </span>
            <span className="summary">{row.summary}</span>
          </span>
        </li>
      ))}
      </ol>
    </>
  );
}
