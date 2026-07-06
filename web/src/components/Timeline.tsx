// SPDX-License-Identifier: GPL-3.0-or-later
import { useApi } from "../context/ApiContext";
import { useAsync } from "../hooks/useAsync";
import { State } from "../ui/State";
import { rowActivation } from "../util/a11y";

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

  return (
    <ol className="timeline" aria-label="timeline">
      {data.map((row) => (
        <li
          key={row.doc_id}
          className={`timeline-row ${onPivot ? "clickable" : ""}`}
          data-dataset={row.dataset}
          aria-label={onPivot ? "open in artifacts" : undefined}
          {...(onPivot ? rowActivation(() => onPivot(row.dataset, row.doc_id)) : {})}
        >
          <time className="ts" dateTime={row.timestamp}>
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
