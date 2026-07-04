// SPDX-License-Identifier: GPL-3.0-or-later
import { useState } from "react";

import type { Case } from "./api/types";
import { Alerts } from "./components/Alerts";
import { ArtifactTable } from "./components/ArtifactTable";
import { CasePicker } from "./components/CasePicker";
import { Overview } from "./components/Overview";
import { Timeline } from "./components/Timeline";

type Tab = "overview" | "artifacts" | "timeline" | "alerts";
const TABS: Tab[] = ["overview", "artifacts", "timeline", "alerts"];

export function App() {
  const [selected, setSelected] = useState<Case | null>(null);
  const [tab, setTab] = useState<Tab>("overview");
  const [dataset, setDataset] = useState<string>("");
  const [highlight, setHighlight] = useState<string | undefined>(undefined);

  function selectCase(c: Case) {
    setSelected(c);
    setDataset(c.datasets[0] ?? "");
    setHighlight(undefined);
    setTab("overview");
  }

  function pivot(ds: string, docId: string) {
    setDataset(ds);
    setHighlight(docId);
    setTab("artifacts");
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>Raptorscope</h1>
        <span className="tagline">macOS DFIR triage</span>
        {selected && (
          <div className="case-badge">
            <span>{selected.name}</span>
            <button className="link" onClick={() => setSelected(null)}>
              change case
            </button>
          </div>
        )}
      </header>

      {!selected ? (
        <main className="pad">
          <h2>Select a case</h2>
          <CasePicker onSelect={selectCase} />
        </main>
      ) : (
        <main className="workspace">
          <nav className="tabs" aria-label="views">
            {TABS.map((t) => (
              <button
                key={t}
                className={t === tab ? "tab active" : "tab"}
                aria-current={t === tab ? "page" : undefined}
                onClick={() => setTab(t)}
              >
                {t}
              </button>
            ))}
          </nav>

          <div className="tab-body">
            {tab === "overview" && <Overview caseName={selected.name} />}

            {tab === "artifacts" && (
              <div>
                <div className="dataset-tabs" aria-label="datasets">
                  {selected.datasets.map((ds) => (
                    <button
                      key={ds}
                      className={ds === dataset ? "chip active" : "chip"}
                      onClick={() => {
                        setDataset(ds);
                        setHighlight(undefined);
                      }}
                    >
                      {ds.replace("macos.", "")}
                    </button>
                  ))}
                </div>
                {dataset && (
                  <ArtifactTable
                    caseName={selected.name}
                    dataset={dataset}
                    highlightId={highlight}
                  />
                )}
              </div>
            )}

            {tab === "timeline" && <Timeline caseName={selected.name} />}

            {tab === "alerts" && (
              <Alerts caseName={selected.name} onPivot={pivot} />
            )}
          </div>
        </main>
      )}
    </div>
  );
}
