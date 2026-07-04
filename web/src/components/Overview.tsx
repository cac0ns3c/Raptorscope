// SPDX-License-Identifier: GPL-3.0-or-later
import { useApi } from "../context/ApiContext";
import { useAsync } from "../hooks/useAsync";

export function Overview({ caseName }: { caseName: string }) {
  const api = useApi();
  const { data, loading, error } = useAsync(
    () => api.getOverview(caseName),
    [caseName],
  );

  if (loading) return <p className="muted">Loading overview…</p>;
  if (error || !data) return <p className="error">Failed to load overview.</p>;

  return (
    <section className="overview" aria-label="overview">
      <div className="tiles">
        {Object.entries(data.datasets).map(([ds, count]) => (
          <div className="tile" key={ds}>
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
                <span>{n}</span>
              </li>
            ))}
          </ul>
        </div>
        <div className="panel">
          <h3>Unsigned</h3>
          <ul className="kv">
            <li>
              <span>processes</span>
              <span className={data.unsigned.process ? "flag" : ""}>
                {data.unsigned.process}
              </span>
            </li>
            <li>
              <span>applications</span>
              <span className={data.unsigned.inventory ? "flag" : ""}>
                {data.unsigned.inventory}
              </span>
            </li>
          </ul>
          <p className="muted">{data.total} documents total</p>
        </div>
      </div>
    </section>
  );
}
