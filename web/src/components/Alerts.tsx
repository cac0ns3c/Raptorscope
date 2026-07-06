// SPDX-License-Identifier: GPL-3.0-or-later
import { useEffect, useState } from "react";

import type { Alert } from "../api/types";
import { useApi } from "../context/ApiContext";
import { useAiEnabled } from "../hooks/useAiEnabled";
import { useAsync } from "../hooks/useAsync";
import { triageKey, useTriage } from "../hooks/useTriage";
import { IconAlert, IconShieldCheck } from "../ui/icons";
import { Markdown } from "../ui/Markdown";

type AiState = Record<string, { loading: boolean; text?: string }>;
const aiTriageKey = (c: string) => `rs_triage:${c}`;
// Severity ordering for the triage queue; unknown levels sort last.
const SEV_ORDER = ["high", "medium", "low"];
const sevRank = (level: string) => {
  const i = SEV_ORDER.indexOf(level);
  return i === -1 ? SEV_ORDER.length : i;
};

function loadTriage(c: string): AiState {
  try {
    const raw = window.localStorage.getItem(aiTriageKey(c));
    if (!raw) return {};
    const saved = JSON.parse(raw) as Record<string, string>;
    return Object.fromEntries(
      Object.entries(saved).map(([k, text]) => [k, { loading: false, text }]),
    );
  } catch {
    return {};
  }
}

function saveTriage(c: string, state: AiState): void {
  try {
    const done = Object.fromEntries(
      Object.entries(state)
        .filter(([, v]) => v.text)
        .map(([k, v]) => [k, v.text]),
    );
    window.localStorage.setItem(aiTriageKey(c), JSON.stringify(done));
  } catch {
    /* ignore storage failures */
  }
}

export function Alerts({
  caseName,
  onPivot,
}: {
  caseName: string;
  onPivot?: (dataset: string, docId: string) => void;
}) {
  const api = useApi();
  const aiEnabled = useAiEnabled();
  const { map, update } = useTriage();
  const [showDismissed, setShowDismissed] = useState(false);
  const [noteOpen, setNoteOpen] = useState<string | null>(null);
  const [ai, setAi] = useState<AiState>({});

  // Restore persisted triage analyses for this case (survive tab/case switches).
  useEffect(() => setAi(loadTriage(caseName)), [caseName]);

  function runTriage(key: string, a: Alert) {
    setAi((s) => ({ ...s, [key]: { loading: true } }));
    api
      .aiTriage(caseName, a.rule_id, a.doc_id)
      .then((r) =>
        setAi((s) => {
          const next = { ...s, [key]: { loading: false, text: r.analysis } };
          saveTriage(caseName, next);
          return next;
        }),
      )
      .catch(() =>
        setAi((s) => ({
          ...s,
          [key]: {
            loading: false,
            text: "AI triage failed — check the provider API key and quota.",
          },
        })),
      );
  }
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
  // Triage queue is severity-first (high → medium → low); the API order isn't.
  const visible = keyed
    .filter(({ key }) => map[key]?.status !== "dismissed" || showDismissed)
    .sort((x, y) => sevRank(x.a.level) - sevRank(y.a.level));
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
                aria-label={`${a.level} severity: ${a.title} — view evidence`}
                onClick={() => onPivot?.(a.dataset, a.doc_id)}
                onKeyDown={(e) => {
                  // Only the card itself pivots — ignore keys bubbling up from
                  // the nested note input / action buttons (e.g. Space while typing).
                  if (e.target !== e.currentTarget) return;
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    onPivot?.(a.dataset, a.doc_id);
                  }
                }}
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
                  {aiEnabled && (
                    <button
                      className="ai-btn"
                      aria-label="AI triage"
                      onClick={() => runTriage(key, a)}
                      disabled={ai[key]?.loading}
                    >
                      {ai[key]?.loading ? "Analyzing…" : "✦ AI triage"}
                    </button>
                  )}
                </div>

                {ai[key]?.text && (
                  <div className="ai-panel" onClick={(e) => e.stopPropagation()}>
                    <Markdown text={ai[key]!.text!} />
                  </div>
                )}

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
