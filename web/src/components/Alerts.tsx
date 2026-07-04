// SPDX-License-Identifier: GPL-3.0-or-later
import { useState } from "react";

import type { Alert } from "../api/types";
import { useApi } from "../context/ApiContext";
import { useAsync } from "../hooks/useAsync";
import { triageKey, useTriage } from "../hooks/useTriage";
import { IconAlert, IconShieldCheck } from "../ui/icons";

export function Alerts({
  caseName,
  onPivot,
}: {
  caseName: string;
  onPivot?: (dataset: string, docId: string) => void;
}) {
  const api = useApi();
  const { map, update } = useTriage();
  const [showDismissed, setShowDismissed] = useState(false);
  const [noteOpen, setNoteOpen] = useState<string | null>(null);
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

  const keyed = data.map((a) => ({ a, key: triageKey(caseName, a) }));
  const dismissed = keyed.filter(({ key }) => map[key]?.status === "dismissed");
  const visible = keyed.filter(
    ({ key }) => map[key]?.status !== "dismissed" || showDismissed,
  );
  const acked = keyed.filter(({ key }) => map[key]?.status === "ack").length;

  return (
    <section aria-label="alerts">
      <div className="alerts-toolbar">
        <span className="muted">
          {keyed.length - dismissed.length} active · {acked} acknowledged ·{" "}
          {dismissed.length} dismissed
        </span>
        {dismissed.length > 0 && (
          <button
            className="btn-change"
            onClick={() => setShowDismissed((s) => !s)}
          >
            {showDismissed ? "hide dismissed" : `show ${dismissed.length} dismissed`}
          </button>
        )}
      </div>

      <ul className="alerts">
        {visible.map(({ a, key }: { a: Alert; key: string }) => {
          const entry = map[key] ?? {};
          return (
            <li key={key}>
              <div
                className={`alert-card sev-${a.level} ${
                  entry.status ? `is-${entry.status}` : ""
                }`}
                role="button"
                tabIndex={0}
                onClick={() => onPivot?.(a.dataset, a.doc_id)}
                onKeyDown={(e) =>
                  e.key === "Enter" && onPivot?.(a.dataset, a.doc_id)
                }
              >
                <span className="alert-ico">
                  <IconAlert />
                </span>
                <span className="alert-head">
                  <span className="level">{a.level}</span>
                  <span className="alert-title">{a.title}</span>
                  {entry.status === "ack" && (
                    <span className="triage-tag ack">acknowledged</span>
                  )}
                  {entry.status === "dismissed" && (
                    <span className="triage-tag dismissed">dismissed</span>
                  )}
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

                <div
                  className="alert-actions"
                  onClick={(e) => e.stopPropagation()}
                >
                  <button
                    onClick={() =>
                      update(key, {
                        status: entry.status === "ack" ? undefined : "ack",
                      })
                    }
                  >
                    {entry.status === "ack" ? "Unack" : "Ack"}
                  </button>
                  <button
                    onClick={() =>
                      update(key, {
                        status:
                          entry.status === "dismissed" ? undefined : "dismissed",
                      })
                    }
                  >
                    {entry.status === "dismissed" ? "Restore" : "Dismiss"}
                  </button>
                  <button
                    onClick={() => setNoteOpen(noteOpen === key ? null : key)}
                  >
                    Note
                  </button>
                </div>

                {(noteOpen === key || entry.note) && (
                  <input
                    className="alert-note"
                    aria-label={`note for ${a.title}`}
                    placeholder="Add a triage note…"
                    value={entry.note ?? ""}
                    onClick={(e) => e.stopPropagation()}
                    onChange={(e) => update(key, { note: e.target.value })}
                  />
                )}
              </div>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
