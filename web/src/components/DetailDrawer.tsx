// SPDX-License-Identifier: GPL-3.0-or-later
import type { Doc } from "../api/types";
import { cell } from "../util/dig";
import { flatten } from "../util/tabular";

export function DetailDrawer({ doc, onClose }: { doc: Doc; onClose: () => void }) {
  const fields = flatten(doc);
  const dataset = String(
    (doc.event as { dataset?: string } | undefined)?.dataset ?? "document",
  );

  return (
    <div className="drawer-overlay" onClick={onClose}>
      <aside
        className="drawer"
        role="dialog"
        aria-label="document detail"
        onClick={(e) => e.stopPropagation()}
      >
        <header className="drawer-head">
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
            {fields.map(([k, v]) => (
              <tr key={k}>
                <th>{k}</th>
                <td className="mono">{cell(v)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </aside>
    </div>
  );
}
