// SPDX-License-Identifier: GPL-3.0-or-later
import { useState } from "react";

import { AuthError } from "../api/client";
import type { Doc, SearchQuery } from "../api/types";
import { useApi } from "../context/ApiContext";
import { useAiEnabled } from "../hooks/useAiEnabled";
import { useAsync } from "../hooks/useAsync";
import { IconSearch } from "../ui/icons";
import { rowActivation } from "../util/a11y";
import { cell, dig } from "../util/dig";

const FIELDS = [
  "file.path",
  "file.name",
  "process.executable",
  "process.command_line",
  "process.name",
  "raptorscope.persistence.type",
  "raptorscope.persistence.label",
  "raptorscope.tcc.service",
  "raptorscope.tcc.client",
  "raptorscope.app.name",
  "url.full",
  "url.original",
  "host.name",
];
const OPS = ["contains", "eq", "startswith", "endswith"];

function primary(doc: Doc): string {
  for (const p of [
    "file.path",
    "process.executable",
    "raptorscope.persistence.label",
    "raptorscope.tcc.service",
    "raptorscope.app.name",
    "url.full",
  ]) {
    const v = dig(doc, p);
    if (v) return cell(v);
  }
  return doc._id;
}

export function Search({
  caseName,
  datasets,
  onPivot,
}: {
  caseName: string;
  datasets: string[];
  onPivot?: (dataset: string, docId: string) => void;
}) {
  const api = useApi();
  const aiEnabled = useAiEnabled();
  const [q, setQ] = useState("");
  const [ds, setDs] = useState("");
  const [field, setField] = useState("");
  const [op, setOp] = useState("contains");
  const [value, setValue] = useState("");
  const [showHelp, setShowHelp] = useState(false);
  const [nl, setNl] = useState("");
  const [nlBusy, setNlBusy] = useState(false);
  const [nlErr, setNlErr] = useState<string | null>(null);
  const [query, setQuery] = useState<SearchQuery | null>(null);

  async function askNl(e: React.FormEvent) {
    e.preventDefault();
    if (!nl.trim()) return;
    setNlBusy(true);
    setNlErr(null);
    try {
      const { query: compiled } = await api.aiNlQuery(caseName, nl);
      setQ(compiled.q ?? "");
      setDs(compiled.dataset ?? "");
      setField(compiled.field ?? "");
      setOp(compiled.op ?? "contains");
      setValue(compiled.value ?? "");
      setQuery({ ...compiled, limit: 200 });
    } catch (err) {
      // AuthError already routes to login via the rs:unauthorized event.
      if (!(err instanceof AuthError)) setNlErr("Couldn't build a query — try rephrasing.");
    } finally {
      setNlBusy(false);
    }
  }

  const { data, loading } = useAsync(
    () => (query ? api.search(caseName, query) : Promise.resolve(null)),
    [caseName, query],
  );

  function run(e: React.FormEvent) {
    e.preventDefault();
    setQuery({
      q,
      dataset: ds || undefined,
      field: field || undefined,
      op: field ? op : undefined,
      value: field ? value : undefined,
      limit: 200,
    });
  }

  return (
    <section className="search">
      {aiEnabled && (
        <form className="nl-bar" onSubmit={askNl}>
          <span className="ai-spark">✦</span>
          <input
            className="q-input"
            aria-label="ask in plain english"
            placeholder="Ask in plain English — e.g. unsigned processes from tmp"
            value={nl}
            onChange={(e) => setNl(e.target.value)}
          />
          <button className="q-run" type="submit" disabled={nlBusy}>
            {nlBusy ? "…" : "Ask"}
          </button>
        </form>
      )}
      {nlErr && (
        <div className="nl-error" role="alert">
          {nlErr}
        </div>
      )}
      <form className="query-bar" onSubmit={run} role="search">
        <span className="q-ico">
          <IconSearch width={16} height={16} />
        </span>
        <input
          className="q-input"
          aria-label="query"
          placeholder="Search paths, commands, labels, URLs…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        <select
          className="q-dataset"
          aria-label="dataset filter"
          value={ds}
          onChange={(e) => setDs(e.target.value)}
        >
          <option value="">All datasets</option>
          {datasets.map((d) => (
            <option key={d} value={d}>
              {d.replace("macos.", "")}
            </option>
          ))}
        </select>
        <button className="q-run" type="submit">
          Search
        </button>
        <button
          type="button"
          className="q-help-toggle"
          aria-label="query help"
          onClick={() => setShowHelp((s) => !s)}
        >
          ?
        </button>
      </form>

      <div className="field-filter" aria-label="field filter">
        <span className="ff-label">Field filter</span>
        <select
          aria-label="filter field"
          value={field}
          onChange={(e) => setField(e.target.value)}
        >
          <option value="">(none)</option>
          {FIELDS.map((f) => (
            <option key={f} value={f}>
              {f}
            </option>
          ))}
        </select>
        <select
          aria-label="filter operator"
          value={op}
          disabled={!field}
          onChange={(e) => setOp(e.target.value)}
        >
          {OPS.map((o) => (
            <option key={o} value={o}>
              {o}
            </option>
          ))}
        </select>
        <input
          aria-label="filter value"
          placeholder="value"
          disabled={!field}
          value={value}
          onChange={(e) => setValue(e.target.value)}
        />
      </div>

      {showHelp && (
        <div className="query-help" role="note" aria-label="query help panel">
          <h4>How to search</h4>
          <ul>
            <li>
              <b>Free text</b> — type any term; it matches <i>anywhere</i> in a
              document (paths, commands, labels, URLs, hostnames). Case-insensitive.
            </li>
            <li>
              <b>Scope by dataset</b> — the dropdown limits results to one artifact
              type (persistence, process, quarantine, tcc, inventory).
            </li>
            <li>
              <b>Field filter</b> — target one ECS field with an operator:
              <code>contains</code>, <code>eq</code> (exact),
              <code> startswith</code>, <code>endswith</code>. Combined with free
              text using AND.
            </li>
          </ul>
          <h4>Examples</h4>
          <table className="help-examples">
            <tbody>
              <tr>
                <td><code>/private/tmp</code></td>
                <td>anything referencing a temp path</td>
              </tr>
              <tr>
                <td><code>com.apple</code> + dataset <code>persistence</code></td>
                <td>Apple-labelled persistence items</td>
              </tr>
              <tr>
                <td>
                  field <code>process.executable</code> <code>startswith</code>{" "}
                  <code>/Users</code>
                </td>
                <td>processes launched from a user directory</td>
              </tr>
              <tr>
                <td>
                  field <code>raptorscope.tcc.service</code> <code>eq</code>{" "}
                  <code>kTCCServiceAccessibility</code>
                </td>
                <td>Accessibility grants</td>
              </tr>
            </tbody>
          </table>
          <p className="muted">
            Click any result to open its full document; the same fields work in
            Kibana's Discover (KQL) against the <code>raptorscope-*</code> index.
          </p>
        </div>
      )}

      {!query && !showHelp && (
        <p className="muted q-hint">
          Enter a term to search every field across this case, or open{" "}
          <b>?</b> for query help.
        </p>
      )}
      {query && loading && (
        <div className="state">
          <span className="spinner" /> Searching…
        </div>
      )}
      {query && !loading && data && (
        <>
          <p className="q-count muted" role="status" aria-live="polite">
            {data.total} {data.total === 1 ? "result" : "results"}
          </p>
          {data.total === 0 ? (
            <p className="muted">No documents match.</p>
          ) : (
            <div className="artifact-view">
              <div className="table-scroll">
                <table className="grid" aria-label="search results">
                  <thead>
                    <tr>
                      <th>Dataset</th>
                      <th>Match</th>
                      <th>Time</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.items.map((doc) => {
                      const dataset = String(dig(doc, "event.dataset") ?? "");
                      return (
                        <tr
                          key={doc._id}
                          data-testid="search-row"
                          className="clickable"
                          aria-label="open in artifacts"
                          {...rowActivation(() => onPivot?.(dataset, doc._id))}
                        >
                          <td>
                            <span className="badge" data-dataset={dataset}>
                              {dataset.replace("macos.", "")}
                            </span>
                          </td>
                          <td className="mono">{primary(doc)}</td>
                          <td className="mono">
                            {cell(dig(doc, "@timestamp"))}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </section>
  );
}
