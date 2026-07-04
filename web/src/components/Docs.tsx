// SPDX-License-Identifier: GPL-3.0-or-later
import { marked } from "marked";
import { useEffect, useMemo, useState } from "react";

import type { DocMeta } from "../api/types";
import { useApi } from "../context/ApiContext";
import { useAsync } from "../hooks/useAsync";

export function Docs({ onClose }: { onClose: () => void }) {
  const api = useApi();
  const [docs, setDocs] = useState<DocMeta[] | null>(null);
  const [active, setActive] = useState<string>("readme");

  useEffect(() => {
    let live = true;
    api.listDocs().then((d) => {
      if (!live) return;
      setDocs(d);
      if (d.length && !d.some((x) => x.id === "readme")) setActive(d[0].id);
    });
    return () => {
      live = false;
    };
  }, [api]);

  const { data } = useAsync(() => api.getDoc(active), [active]);
  const html = useMemo(
    () => (data ? marked.parse(data.markdown) : ""),
    [data],
  );

  return (
    <div className="docs-overlay" role="dialog" aria-label="documentation">
      <div className="docs-panel">
        <aside className="docs-nav">
          <div className="docs-nav-head">
            <span>Documentation</span>
            <button className="docs-close" aria-label="close docs" onClick={onClose}>
              ✕
            </button>
          </div>
          <ul>
            {(docs ?? []).map((d) => (
              <li key={d.id}>
                <button
                  className={d.id === active ? "docs-link active" : "docs-link"}
                  onClick={() => setActive(d.id)}
                >
                  {d.title}
                </button>
              </li>
            ))}
          </ul>
        </aside>
        <article
          className="docs-content markdown"
          // Trusted content: our own repo docs served by the backend.
          dangerouslySetInnerHTML={{ __html: html as string }}
        />
      </div>
    </div>
  );
}
