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

  if (loading) return <p className="muted">Loading timeline…</p>;
  if (error || !data) return <p className="error">Failed to load timeline.</p>;
  if (data.length === 0) return <p className="muted">No events.</p>;

  return (
    <ol className="timeline" aria-label="timeline">
      {data.map((row) => (
        <li key={row.doc_id} className="timeline-row">
          <time className="ts" data-testid="tl-ts">
            {row.timestamp}
          </time>
          <span className="badge" data-dataset={row.dataset}>
            {row.dataset.replace("macos.", "")}
          </span>
          <span className="summary">{row.summary}</span>
        </li>
      ))}
    </ol>
  );
}
