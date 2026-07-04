// SPDX-License-Identifier: GPL-3.0-or-later
import type { Alert } from "../api/types";
import { useApi } from "../context/ApiContext";
import { useAsync } from "../hooks/useAsync";
import { IconAlert, IconShieldCheck } from "../ui/icons";

export function Alerts({
  caseName,
  onPivot,
}: {
  caseName: string;
  onPivot?: (dataset: string, docId: string) => void;
}) {
  const api = useApi();
  const { data, loading, error } = useAsync(
    () => api.getAlerts(caseName),
    [caseName],
  );

  if (loading)
    return (
      <div className="state">
        <span className="spinner" /> Loading alerts…
      </div>
    );
  if (error || !data) return <p className="error">Failed to load alerts.</p>;
  if (data.length === 0)
    return (
      <div className="empty-clear">
        <IconShieldCheck />
        No detections fired for this case.
      </div>
    );

  return (
    <ul className="alerts" aria-label="alerts">
      {data.map((a: Alert, i) => (
        <li key={`${a.rule_id}-${a.doc_id}-${i}`}>
          <button
            className={`alert-card sev-${a.level}`}
            onClick={() => onPivot?.(a.dataset, a.doc_id)}
          >
            <span className="alert-ico">
              <IconAlert />
            </span>
            <span className="alert-head">
              <span className="level">{a.level}</span>
              <span className="alert-title">{a.title}</span>
              <span className="alert-dataset">
                {a.dataset.replace("macos.", "")}
              </span>
            </span>
            <span className="alert-evidence">
              {Object.entries(a.evidence).map(([k, v]) => (
                <code key={k}>
                  {k}={String(v)}
                </code>
              ))}
            </span>
          </button>
        </li>
      ))}
    </ul>
  );
}
