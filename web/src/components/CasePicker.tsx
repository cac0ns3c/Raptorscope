// SPDX-License-Identifier: GPL-3.0-or-later
import { useEffect, useState } from "react";

import type { Case } from "../api/types";
import { useApi } from "../context/ApiContext";
import { IconChevronRight, IconHost } from "../ui/icons";

export function CasePicker({ onSelect }: { onSelect: (c: Case) => void }) {
  const api = useApi();
  const [cases, setCases] = useState<Case[] | null>(null);

  useEffect(() => {
    let live = true;
    api.listCases().then((c) => live && setCases(c));
    return () => {
      live = false;
    };
  }, [api]);

  if (cases === null) {
    return (
      <div className="state">
        <span className="spinner" /> Loading cases…
      </div>
    );
  }
  if (cases.length === 0) {
    return (
      <div className="empty-cases">
        <IconHost width={26} height={26} />
        <p className="muted">No cases yet.</p>
        <code>raptorscope ingest &lt;collection&gt; --es …</code>
      </div>
    );
  }

  const totalDocs = cases.reduce((s, c) => s + c.doc_count, 0);

  return (
    <div className="case-picker">
      <p className="case-summary muted">
        {cases.length} {cases.length === 1 ? "host" : "hosts"} ·{" "}
        {totalDocs.toLocaleString()} documents
      </p>
      <ul className="case-list" aria-label="cases">
        {cases.map((c) => (
          <li key={c.name}>
            <button className="case-card" onClick={() => onSelect(c)}>
              <span className="case-top">
                <span className="case-ico">
                  <IconHost width={20} height={20} />
                </span>
                <span className="case-id">
                  <span className="case-name">{c.name}</span>
                  <span className="case-meta">
                    <b>{c.doc_count} docs</b> · {c.datasets.length} datasets
                  </span>
                </span>
                <span className="chev">
                  <IconChevronRight />
                </span>
              </span>
              <span className="ds-row">
                {c.datasets.map((ds) => (
                  <span className="ds-tag" data-dataset={ds} key={ds}>
                    <i className="dot" />
                    {ds.replace("macos.", "")}
                  </span>
                ))}
              </span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
