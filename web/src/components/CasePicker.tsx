// SPDX-License-Identifier: GPL-3.0-or-later
import { useEffect, useState } from "react";

import type { Case } from "../api/types";
import { useApi } from "../context/ApiContext";

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
    return <p className="muted">Loading cases…</p>;
  }
  if (cases.length === 0) {
    return <p className="muted">No cases. Ingest a collection to begin.</p>;
  }

  return (
    <ul className="case-list" aria-label="cases">
      {cases.map((c) => (
        <li key={c.name}>
          <button className="case-card" onClick={() => onSelect(c)}>
            <span className="case-name">{c.name}</span>
            <span className="case-meta">{c.doc_count} docs</span>
            <span className="case-datasets">{c.datasets.length} datasets</span>
          </button>
        </li>
      ))}
    </ul>
  );
}
