// SPDX-License-Identifier: GPL-3.0-or-later
import { useState } from "react";

import type { Doc, SearchQuery } from "../api/types";
import { useApi } from "../context/ApiContext";
import { useAsync } from "../hooks/useAsync";
import { IconSearch } from "../ui/icons";
import { cell, dig } from "../util/dig";

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
  const [q, setQ] = useState("");
  const [ds, setDs] = useState("");
  const [query, setQuery] = useState<SearchQuery | null>(null);

  const { data, loading } = useAsync(
    () => (query ? api.search(caseName, query) : Promise.resolve(null)),
    [caseName, query],
  );

  function run(e: React.FormEvent) {
    e.preventDefault();
    setQuery({ q, dataset: ds || undefined, limit: 200 });
  }

  return (
    <section className="search">
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
      </form>

      {!query && (
        <p className="muted q-hint">
          Enter a term to search every field across this case.
        </p>
      )}
      {query && loading && (
        <div className="state">
          <span className="spinner" /> Searching…
        </div>
      )}
      {query && !loading && data && (
        <>
          <p className="q-count muted">
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
                          onClick={() => onPivot?.(dataset, doc._id)}
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
