// SPDX-License-Identifier: GPL-3.0-or-later
import { useState } from "react";

import type { Case } from "./api/types";
import { Alerts } from "./components/Alerts";
import { ArtifactTable } from "./components/ArtifactTable";
import { CasePicker } from "./components/CasePicker";
import { Copilot } from "./components/Copilot";
import { Docs } from "./components/Docs";
import { Overview } from "./components/Overview";
import { Search } from "./components/Search";
import { Timeline } from "./components/Timeline";
import { useAuthSession } from "./context/AuthSessionContext";
import { useAiEnabled } from "./hooks/useAiEnabled";
import { useTheme } from "./hooks/useTheme";
import {
  IconBell,
  IconClock,
  IconGauge,
  IconHost,
  IconLayers,
  IconLogo,
  IconSearch,
  IconSpark,
} from "./ui/icons";
import { kibanaBase, kibanaDiscoverUrl } from "./util/kibana";

type Tab = "overview" | "artifacts" | "timeline" | "alerts" | "search" | "copilot";
const BASE_TABS: { id: Tab; icon: JSX.Element }[] = [
  { id: "overview", icon: <IconGauge /> },
  { id: "artifacts", icon: <IconLayers /> },
  { id: "timeline", icon: <IconClock /> },
  { id: "alerts", icon: <IconBell /> },
  { id: "search", icon: <IconSearch /> },
];

export function App() {
  const [selected, setSelected] = useState<Case | null>(null);
  const [tab, setTab] = useState<Tab>("overview");
  const [dataset, setDataset] = useState<string>("");
  const [highlight, setHighlight] = useState<string | undefined>(undefined);
  const [showDocs, setShowDocs] = useState(false);
  const { theme, toggle } = useTheme();
  const { gated, logout } = useAuthSession();
  const aiEnabled = useAiEnabled();
  const TABS = aiEnabled
    ? [...BASE_TABS, { id: "copilot" as Tab, icon: <IconSpark /> }]
    : BASE_TABS;

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
      <header className="topbar">
        <div className="brand">
          <span className="logo">
            <IconLogo />
          </span>
          <h1>Raptorscope</h1>
          <span className="tagline">macOS DFIR triage</span>
        </div>
        <div className="topbar-actions">
          <button
            className="btn-change"
            aria-label="toggle theme"
            onClick={toggle}
          >
            {theme === "dark" ? "☀" : "☾"}
          </button>
          <button className="btn-change" onClick={() => setShowDocs(true)}>
            Docs
          </button>
          {gated && (
            <button className="btn-change" onClick={logout}>
              Sign out
            </button>
          )}
          {selected && (
          <div className="case-context">
            <span className="host-ico">
              <IconHost width={16} height={16} />
            </span>
            <span className="host-name">{selected.name}</span>
            {kibanaBase() && (
              <a
                className="btn-change kibana-link"
                href={kibanaDiscoverUrl(kibanaBase(), selected.name)}
                target="_blank"
                rel="noreferrer"
              >
                Kibana ↗
              </a>
            )}
            <button className="btn-change" onClick={() => setSelected(null)}>
              change case
            </button>
          </div>
          )}
        </div>
      </header>

      {showDocs && <Docs onClose={() => setShowDocs(false)} />}

      {!selected ? (
        <main className="content landing">
          <div className="hero">
            <span className="hero-mark">
              <IconLogo width={26} height={26} />
            </span>
            <h2>Select a case</h2>
            <p>Choose a collected macOS host to begin first-hour triage.</p>
          </div>
          <CasePicker onSelect={selectCase} />
        </main>
      ) : (
        <main className="content">
          <nav className="tabs" aria-label="views">
            {TABS.map((t) => (
              <button
                key={t.id}
                className={t.id === tab ? "tab active" : "tab"}
                aria-current={t.id === tab ? "page" : undefined}
                onClick={() => setTab(t.id)}
              >
                <span className="tab-ico">{t.icon}</span>
                {t.id}
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
                      data-dataset={ds}
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

            {tab === "search" && (
              <Search
                caseName={selected.name}
                datasets={selected.datasets}
                onPivot={pivot}
              />
            )}

            {tab === "copilot" && <Copilot caseName={selected.name} />}
          </div>
        </main>
      )}
    </div>
  );
}
