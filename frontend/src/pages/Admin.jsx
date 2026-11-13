import "./Admin.css";
import { useEffect, useState } from "react";
import { Pie } from "react-chartjs-2";
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from "chart.js";
import { useI18n } from "../i18n";
import { getStats } from "../api/admin.js";

ChartJS.register(ArcElement, Tooltip, Legend);

// Wraps each value in quotes and doubles any quote inside it, so commas don't break the columns.
function csvCell(value) {
  const text = String(value ?? "");
  return `"${text.replace(/"/g, '""')}"`;
}

// Builds a CSV file from the table rows and downloads it.
function downloadCsv(rows) {
  const header = ["domain", "count", "firstSeen", "risk", "status"].map(csvCell).join(",");
  const lines = rows.map((r) =>
    [r.domain, r.count, r.firstSeen, r.risk, r.status].map(csvCell).join(",")
  );
  const blob = new Blob([[header, ...lines].join("\n")], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "genzura-trending-domains.csv";
  a.click();
  URL.revokeObjectURL(url);
}

export default function Admin() {
  const { t } = useI18n();
  const [stats, setStats] = useState(null);
  const [status, setStatus] = useState("loading");
  const [domains] = useState([]);

  useEffect(() => {
    let cancelled = false;
    getStats()
      .then((data) => {
        if (!cancelled) {
          setStats(data);
          setStatus("ready");
        }
      })
      .catch((err) => {
        if (cancelled) return;
        setStatus(err.status === 401 || err.status === 403 ? "denied" : "error");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  let content;
  if (status === "loading") {
    content = <p className="section-intro">{t("admin.loading")}</p>;
  } else if (status === "error") {
    content = <p className="section-intro">{t("admin.error")}</p>;
  } else if (status === "denied") {
    content = <p className="section-intro">{t("admin.signInRequired")}</p>;
  } else if (stats.total === 0) {
    content = <p className="section-intro">{t("admin.noData")}</p>;
  } else {
    const byVerdict = stats.by_verdict || {};
    const byContext = stats.by_context || {};
    const pieData = {
      labels: [t("offerType.job"), t("offerType.scholarship"), t("offerType.visa")],
      datasets: [
        {
          data: [byContext.job || 0, byContext.scholarship || 0, byContext.visa || 0],
          backgroundColor: ["#d4af37", "#f5f1e6", "#8a9bb5"],
        },
      ],
    };

    content = (
      <>
        <div className="kpi-grid">
          <div className="kpi"><span>{t("admin.totalChecks")}</span><strong>{stats.total.toLocaleString()}</strong></div>
          <div className="kpi"><span>{t("admin.highRisk")}</span><strong>{(byVerdict.high_risk || 0).toLocaleString()}</strong></div>
          <div className="kpi"><span>{t("admin.suspicious")}</span><strong>{(byVerdict.suspicious || 0).toLocaleString()}</strong></div>
        </div>

        <h3>{t("admin.checksPerDay")}</h3>
        {stats.per_day.length === 0 ? (
          <p className="section-intro">{t("admin.noData")}</p>
        ) : (
          <ul>
            {stats.per_day.map((d) => (
              <li key={d.day}>{d.day}: {d.count}</li>
            ))}
          </ul>
        )}

        <h3>{t("admin.scamTypes")}</h3>
        <div className="pie">
          <Pie data={pieData} />
        </div>

        <h3>{t("admin.topFlags")}</h3>
        {stats.top_flags.length === 0 ? (
          <p className="section-intro">{t("admin.noData")}</p>
        ) : (
          <ol>
            {stats.top_flags.map((f) => (
              <li key={f.flag}>{t(`flags.${f.flag}`)}: {f.count}</li>
            ))}
          </ol>
        )}
      </>
    );
  }

  return (
    <div className="admin">
      <h2 className="section-title">{t("admin.title")}</h2>
      <p className="section-intro">{t("admin.intro")}</p>

      {content}

      <h3>{t("admin.trendingDomains")}</h3>
      {domains.length === 0 ? (
        <p className="section-intro">{t("admin.noData")}</p>
      ) : (
        <>
          <button type="button" onClick={() => downloadCsv(domains)}>{t("admin.downloadCsv")}</button>
          <table className="domains">
            <thead>
              <tr>
                <th>Domain</th>
                <th>Count</th>
                <th>First seen</th>
                <th>Risk</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {domains.map((d) => (
                <tr key={d.domain}>
                  <td>{d.domain}</td>
                  <td>{d.count}</td>
                  <td>{d.firstSeen}</td>
                  <td>{d.risk}</td>
                  <td>{d.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </div>
  );
}