// SPDX-License-Identifier: GPL-3.0-or-later
import { useState } from "react";

import type { Doc } from "../api/types";
import { useModalA11y } from "../hooks/useModalA11y";
import { cell } from "../util/dig";
import { fmtTime } from "../util/format";
import { flatten } from "../util/tabular";

export function DetailDrawer({ doc, onClose }: { doc: Doc; onClose: () => void }) {
  const fields = flatten(doc);
  const dataset = String(
    (doc.event as { dataset?: string } | undefined)?.dataset ?? "document",
  );
  const ref = useModalA11y<HTMLElement>(onClose);
  const [copied, setCopied] = useState<string | null>(null);

  function copyField(key: string, value: string) {
    navigator.clipboard?.writeText(value);
    setCopied(key);
    window.setTimeout(() => setCopied((c) => (c === key ? null : c)), 1200);
  }

  return (
    <div className="drawer-overlay" onClick={onClose}>
      <aside
        ref={ref}
        className="drawer"
        role="dialog"
        aria-modal="true"
        aria-labelledby="drawer-title"
        tabIndex={-1}
        onClick={(e) => e.stopPropagation()}
      >
        <header className="drawer-head" id="drawer-title">
          <span className="badge" data-dataset={dataset}>
            {dataset.replace("macos.", "")}
          </span>
          <span className="drawer-id">#{doc._id}</span>
          <button className="docs-close" aria-label="close detail" onClick={onClose}>
            ✕
          </button>
        </header>
        <table className="detail-grid">
          <tbody>
            {fields.map(([k, v]) => {
              const text = k === "@timestamp" ? fmtTime(String(v)) : cell(v);
              return (
                <tr key={k}>
                  <th>{k}</th>
                  <td className="mono">
                    <span className="detail-val">{text}</span>
                    {text && (
                      <button
                        className="copy-btn"
                        aria-label={`copy ${k}`}
                        title="Copy value"
                        onClick={() => copyField(k, text)}
                      >
                        {copied === k ? "✓" : "⧉"}
                      </button>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </aside>
    </div>
  );
}
