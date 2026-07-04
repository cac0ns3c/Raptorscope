// SPDX-License-Identifier: GPL-3.0-or-later
import { useApi } from "../context/ApiContext";
import { useAsync } from "../hooks/useAsync";

export function Timeline({
  caseName,
  limit = 200,
}: {
  caseName: string;
  limit?: number;
}) {
  const api = useApi();
  const { data, loading, error } = useAsync(
    () => api.getTimeline(caseName, limit),
    [caseName, limit],
  );

  if (loading)
    return (
      <div className="state">
        <span className="spinner" /> Loading timeline…
      </div>
    );
  if (error || !data) return <p className="error">Failed to load timeline.</p>;
  if (data.length === 0) return <p className="muted">No events.</p>;

  return (
    <ol className="timeline" aria-label="timeline">
      {data.map((row) => (
        <li key={row.doc_id} className="timeline-row" data-dataset={row.dataset}>
          <time className="ts">
            <span data-testid="tl-ts">{row.timestamp}</span>
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
  );
}
