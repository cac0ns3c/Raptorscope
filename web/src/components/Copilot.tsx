// SPDX-License-Identifier: GPL-3.0-or-later
import { useState } from "react";

import type { CopilotResult } from "../api/types";
import { useApi } from "../context/ApiContext";
import { Markdown } from "../ui/Markdown";

export function Copilot({ caseName }: { caseName: string }) {
  const api = useApi();
  const [question, setQuestion] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<CopilotResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function ask(e: React.FormEvent) {
    e.preventDefault();
    if (!question.trim()) return;
    setBusy(true);
    setError(null);
    try {
      setResult(await api.aiCopilot(caseName, question));
    } catch {
      setError("The copilot request failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="copilot" aria-label="copilot">
      <p className="muted">
        Ask the investigation copilot a question. It queries this case's evidence
        (search, alerts, overview) and returns a grounded triage verdict.
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

      {busy && (
        <div className="state">
          <span className="spinner" /> The copilot is gathering evidence…
        </div>
      )}
      {error && <p className="error">{error}</p>}
      {result && !busy && (
        <div className="copilot-result">
          <Markdown text={result.answer} />
          {result.citations.length > 0 && (
            <div className="citations">
              <span className="citations-label">Evidence gathered</span>
              <ul>
                {result.citations.map((c, i) => (
                  <li key={i}>
                    <code>{c.tool}</code>
                    {Object.keys(c.input).length > 0 && (
                      <span className="cite-input">
                        {" "}
                        {JSON.stringify(c.input)}
                      </span>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </section>
  );
}
