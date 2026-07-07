// SPDX-License-Identifier: GPL-3.0-or-later
import { useEffect, useRef, useState } from "react";

import type { Column } from "./columns";

export function ColumnPicker({
  available,
  visible,
  toggle,
  reset,
}: {
  available: Column[];
  visible: Set<string>;
  toggle: (path: string) => void;
  reset: () => void;
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onDoc = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    const onEsc = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    document.addEventListener("mousedown", onDoc);
    document.addEventListener("keydown", onEsc);
    return () => {
      document.removeEventListener("mousedown", onDoc);
      document.removeEventListener("keydown", onEsc);
    };
  }, [open]);

  return (
    <div className="col-picker" ref={ref}>
      <button
        className="col-picker-btn"
        aria-haspopup="true"
        aria-expanded={open}
        onClick={() => setOpen((o) => !o)}
      >
        Columns <span aria-hidden="true">▾</span>
      </button>
      {open && (
        <div className="col-picker-menu" role="group" aria-label="choose columns">
          <div className="col-picker-head">
            <span className="muted">{visible.size} shown</span>
            <button className="btn-change" onClick={reset}>
              reset
            </button>
          </div>
          <ul>
            {available.map((c) => (
              <li key={c.path}>
                <label>
                  <input
                    type="checkbox"
                    checked={visible.has(c.path)}
                    onChange={() => toggle(c.path)}
                  />
                  <span className="col-picker-label">{c.header}</span>
                  <span className="col-picker-path">{c.path}</span>
                </label>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
