// SPDX-License-Identifier: GPL-3.0-or-later
import { useEffect, useState } from "react";

import type { Case, HuntResult } from "../api/types";
import { useApi } from "../context/ApiContext";
import { IconChevronRight, IconHost, IconSearch } from "../ui/icons";

export function CasePicker({ onSelect }: { onSelect: (c: Case) => void }) {
  const api = useApi();
  const [cases, setCases] = useState<Case[] | null>(null);
  const [ioc, setIoc] = useState("");
  const [hunt, setHunt] = useState<HuntResult | null>(null);
  const [hunting, setHunting] = useState(false);

  useEffect(() => {
    let live = true;
    api.listCases().then((c) => live && setCases(c));
    return () => {
      live = false;
    };
  }, [api]);

  async function runHunt(e: React.FormEvent) {
    e.preventDefault();
    if (!ioc.trim()) return;
    setHunting(true);
    try {
      setHunt(await api.hunt(ioc.trim()));
    } finally {
      setHunting(false);
    }
  }

  function openHost(name: string) {
    const c = (cases ?? []).find((x) => x.name === name);
    if (c) onSelect(c);
  }

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

      <form className="fleet-hunt" onSubmit={runHunt} role="search">
        <IconSearch width={16} height={16} />
        <input
          className="q-input"
          aria-label="hunt indicator across hosts"
          placeholder="Hunt an IOC across all hosts — IP, path, hash…"
          value={ioc}
          onChange={(e) => setIoc(e.target.value)}
        />
        <button className="q-run" type="submit" disabled={hunting}>
          {hunting ? "Hunting…" : "Hunt"}
        </button>
      </form>

      {hunt && !hunting && (
        <div className="hunt-result" aria-label="hunt result">
          {hunt.host_count === 0 ? (
            <p className="muted">
              No host has <code>{hunt.value}</code>.
            </p>
          ) : (
            <>
              <p className="muted">
                <code>{hunt.value}</code> found on <b>{hunt.host_count}</b> of{" "}
                {cases.length} hosts · {hunt.total} hits
              </p>
              <ul className="hunt-hosts">
                {hunt.hosts.map((h) => (
                  <li key={h.host}>
                    <button className="hunt-host" onClick={() => openHost(h.host)}>
                      <span className="hunt-host-name">{h.host}</span>
                      <span className="hunt-host-meta">
                        <b>{h.count} hits</b> ·{" "}
                        {h.datasets.map((d) => d.replace("macos.", "")).join(", ")}
                      </span>
                      <IconChevronRight />
                    </button>
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>
      )}

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
