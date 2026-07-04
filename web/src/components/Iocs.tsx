// SPDX-License-Identifier: GPL-3.0-or-later
import { useState } from "react";

import type { HuntResult, IOC } from "../api/types";
import { useApi } from "../context/ApiContext";

export function Iocs({ caseName }: { caseName: string }) {
  const api = useApi();
  const [iocs, setIocs] = useState<IOC[] | null>(null);
  const [busy, setBusy] = useState(false);
  const [hunts, setHunts] = useState<Record<string, HuntResult | "loading">>({});

  async function extract() {
    setBusy(true);
    try {
      setIocs((await api.aiIocs(caseName)).iocs);
    } catch {
      setIocs([]);
    } finally {
      setBusy(false);
    }
  }

  async function huntIoc(value: string) {
    setHunts((s) => ({ ...s, [value]: "loading" }));
    try {
      const res = await api.hunt(value);
      setHunts((s) => ({ ...s, [value]: res }));
    } catch {
      setHunts((s) => {
        const n = { ...s };
        delete n[value];
        return n;
      });
    }
  }

  return (
    <div className="iocs">
      <button className="ai-btn" onClick={extract} disabled={busy}>
        {busy ? "Extracting…" : iocs ? "✦ Re-extract IOCs (AI)" : "✦ Extract IOCs (AI)"}
      </button>

      {iocs && iocs.length === 0 && (
        <p className="muted">No indicators extracted.</p>
      )}
      {iocs && iocs.length > 0 && (
        <ul className="ioc-list" aria-label="iocs">
          {iocs.map((ioc) => {
            const h = hunts[ioc.value];
            return (
              <li key={`${ioc.type}:${ioc.value}`} className="ioc-row">
                <span className="ioc-type" data-type={ioc.type}>
                  {ioc.type}
                </span>
                <code className="ioc-value">{ioc.value}</code>
                <span className="ioc-context">{ioc.context}</span>
                <button
                  className="ioc-hunt"
                  onClick={() => huntIoc(ioc.value)}
                  disabled={h === "loading"}
                >
                  {h === "loading" ? "…" : "Hunt fleet"}
                </button>
                {h && h !== "loading" && (
                  <span className="ioc-hunt-result">
                    {h.host_count === 0
                      ? "not seen elsewhere"
                      : `on ${h.host_count} host${h.host_count > 1 ? "s" : ""}: ${h.hosts
                          .map((x) => x.host)
                          .join(", ")}`}
                  </span>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
