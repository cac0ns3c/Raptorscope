// SPDX-License-Identifier: GPL-3.0-or-later
import { useState } from "react";

import type { Citation } from "../api/types";
import { useApi } from "../context/ApiContext";
import { Markdown } from "../ui/Markdown";

export function Copilot({ caseName }: { caseName: string }) {
  const api = useApi();
  const [question, setQuestion] = useState("");
  const [busy, setBusy] = useState(false);
  const [answer, setAnswer] = useState("");
  const [citations, setCitations] = useState<Citation[]>([]);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function ask(e: React.FormEvent) {
    e.preventDefault();
    if (!question.trim()) return;
    setBusy(true);
    setError(null);
    setAnswer("");
    setCitations([]);
    setDone(false);
    let acc = "";
    try {
      await api.aiCopilotStream(caseName, question, (ev) => {
        if (ev.type === "tool") {
          setCitations((c) => [...c, { tool: ev.tool, input: ev.input }]);
        } else if (ev.type === "text") {
          acc += ev.text;
          setAnswer(acc); // stream the verdict token by token
        }
      });
      setDone(true);
    } catch {
      setError("The copilot request failed — check the provider API key and quota.");
    } finally {
      setBusy(false);
    }
  }

  const showResult = citations.length > 0 || answer;

  return (
    <section className="copilot" aria-label="copilot">
      <p className="muted">
        Ask the investigation copilot a question. It queries this case's evidence
        (search, alerts, overview) and returns a grounded triage verdict — live.
      </p>
      <form className="query-bar" onSubmit={ask} role="search">
        <input
          className="q-input"
          aria-label="copilot question"
          placeholder="e.g. Is this host compromised, and how?"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
        />
        <button className="q-run" type="submit" disabled={busy}>
          {busy ? "Investigating…" : "Ask"}
        </button>
      </form>

      {error && <p className="error">{error}</p>}
      {showResult && (
        <div className="copilot-result">
          {citations.length > 0 && (
            <div className="citations">
              <span className="citations-label">
                Evidence gathered{busy && !done ? "…" : ""}
              </span>
              <ul>
                {citations.map((c, i) => (
                  <li key={i}>
                    <code>{c.tool}</code>
                    {Object.keys(c.input).length > 0 && (
                      <span className="cite-input"> {JSON.stringify(c.input)}</span>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {answer && <Markdown text={answer} />}
        </div>
      )}
      {busy && !answer && (
        <div className="state">
          <span className="spinner" /> The copilot is gathering evidence…
        </div>
      )}
    </section>
  );
}
