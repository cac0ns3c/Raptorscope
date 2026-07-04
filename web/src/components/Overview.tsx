// SPDX-License-Identifier: GPL-3.0-or-later
import { useApi } from "../context/ApiContext";
import { useAsync } from "../hooks/useAsync";

export function Overview({ caseName }: { caseName: string }) {
  const api = useApi();
  const { data, loading, error } = useAsync(
    () => api.getOverview(caseName),
    [caseName],
  );

  if (loading)
    return (
      <div className="state">
        <span className="spinner" /> Loading overview…
      </div>
    );
  if (error || !data) return <p className="error">Failed to load overview.</p>;

  const maxType = Math.max(1, ...Object.values(data.persistence_types));

  return (
    <section className="overview" aria-label="overview">
      <div className="tiles">
        {Object.entries(data.datasets).map(([ds, count]) => (
          <div className="tile" data-dataset={ds} key={ds}>
            <span className="tile-count">{count}</span>
            <span className="tile-label">{ds.replace("macos.", "")}</span>
          </div>
        ))}
      </div>

      <div className="panels">
        <div className="panel">
          <h3>Persistence by type</h3>
          <ul className="kv" aria-label="persistence types">
            {Object.entries(data.persistence_types).map(([t, n]) => (
              <li key={t}>
                <span>{t}</span>
                <span className="bar">
                  <span
                    className="bar-fill"
                    style={{ width: `${(n / maxType) * 100}%` }}
                  />
                </span>
                <span>{n}</span>
              </li>
            ))}
          </ul>
        </div>
        <div className="panel">
          <h3>Signing integrity</h3>
          <ul className="integrity">
            <li>
              <span className="metric">Unsigned processes</span>
              <span className={`count ${data.unsigned.process ? "flag" : ""}`}>
                {data.unsigned.process}
              </span>
            </li>
            <li>
              <span className="metric">Unsigned applications</span>
              <span
                className={`count ${data.unsigned.inventory ? "flag" : ""}`}
              >
                {data.unsigned.inventory}
              </span>
            </li>
          </ul>
          <p className="total-line">{data.total} documents total</p>
        </div>
      </div>
    </section>
  );
}
