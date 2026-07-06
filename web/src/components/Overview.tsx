// SPDX-License-Identifier: GPL-3.0-or-later
import { useEffect, useState } from "react";

import { useApi } from "../context/ApiContext";
import { useAiEnabled } from "../hooks/useAiEnabled";
import { useAsync } from "../hooks/useAsync";
import { fmtNum } from "../util/format";
import { Markdown } from "../ui/Markdown";
import { State } from "../ui/State";
import { Iocs } from "./Iocs";

const summaryKey = (c: string) => `rs_summary:${c}`;

function loadSummary(c: string): string | undefined {
  try {
    return window.localStorage.getItem(summaryKey(c)) ?? undefined;
  } catch {
    return undefined;
  }
}

export function Overview({
  caseName,
  onOpenDataset,
}: {
  caseName: string;
  onOpenDataset?: (dataset: string) => void;
}) {
  const api = useApi();
  const aiEnabled = useAiEnabled();
  const [summary, setSummary] = useState<{ loading: boolean; text?: string }>();

  // Restore a previously generated summary for this case; it persists across
  // tab/case switches and reloads until the analyst re-runs it.
  useEffect(() => {
    const cached = loadSummary(caseName);
    setSummary(cached ? { loading: false, text: cached } : undefined);
  }, [caseName]);

  const { data, loading, error, reload } = useAsync(
    () => api.getOverview(caseName),
    [caseName],
  );

  function summarize() {
    setSummary({ loading: true, text: "" });
    let acc = "";
    api
      .aiSummaryStream(caseName, (chunk) => {
        acc += chunk;
        setSummary({ loading: true, text: acc }); // render incrementally
      })
      .then(() => {
        setSummary({ loading: false, text: acc });
        try {
          window.localStorage.setItem(summaryKey(caseName), acc);
        } catch {
          /* ignore storage failures */
        }
      })
      .catch(() =>
        setSummary({
          loading: false,
          text: acc || "AI summary failed — check the provider API key and quota.",
        }),
      );
  }

  if (loading) return <State variant="loading" message="Loading overview…" />;
  if (error || !data)
    return (
      <State
        variant="error"
        message="Failed to load the overview."
        onRetry={reload}
      />
    );

  const maxType = Math.max(1, ...Object.values(data.persistence_types));

  return (
    <section className="overview" aria-label="overview">
      {aiEnabled && (
        <div className="ai-summary">
          <button
            className="ai-btn"
            onClick={summarize}
            disabled={summary?.loading}
          >
            {summary?.loading
              ? "Summarizing…"
              : summary?.text
                ? "✦ Re-summarize case (AI)"
                : "✦ Summarize case (AI)"}
          </button>
          {summary?.text && (
            <div className="ai-panel">
              <Markdown text={summary.text} />
            </div>
          )}
          <Iocs caseName={caseName} />
        </div>
      )}

      <div className="tiles">
        {Object.entries(data.datasets).map(([ds, count]) => (
          <button
            className="tile"
            data-dataset={ds}
            key={ds}
            onClick={() => onOpenDataset?.(ds)}
            aria-label={`view ${count} ${ds.replace("macos.", "")} artifacts`}
          >
            <span className="tile-count">{fmtNum(count)}</span>
            <span className="tile-label">{ds.replace("macos.", "")}</span>
          </button>
        ))}
      </div>

      <div className="panels">
        <div className="panel">
          <h3>Persistence by type</h3>
          <ul className="kv" aria-label="persistence types">
            {Object.entries(data.persistence_types).map(([t, n]) => (
              <li key={t}>
                <span>{t}</span>
                <span className="bar">
                  <span
                    className="bar-fill"
                    style={{ width: `${(n / maxType) * 100}%` }}
                  />
                </span>
                <span>{n}</span>
              </li>
            ))}
          </ul>
        </div>
        <div className="panel">
          <h3>Signing integrity</h3>
          <ul className="integrity">
            <li>
              <button
                className="integrity-row"
                onClick={() => onOpenDataset?.("macos.process")}
                aria-label={`view ${data.unsigned.process} unsigned processes`}
              >
                <span className="metric">Unsigned processes</span>
                <span className={`count ${data.unsigned.process ? "flag" : ""}`}>
                  {fmtNum(data.unsigned.process)}
                </span>
              </button>
            </li>
            <li>
              <button
                className="integrity-row"
                onClick={() => onOpenDataset?.("macos.inventory")}
                aria-label={`view ${data.unsigned.inventory} unsigned applications`}
              >
                <span className="metric">Unsigned applications</span>
                <span
                  className={`count ${data.unsigned.inventory ? "flag" : ""}`}
                >
                  {fmtNum(data.unsigned.inventory)}
                </span>
              </button>
            </li>
          </ul>
          <p className="total-line">{fmtNum(data.total)} documents total</p>
        </div>
      </div>
    </section>
  );
}
