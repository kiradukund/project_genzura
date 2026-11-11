import "./Admin.css";
import { useState } from "react";
import { useI18n } from "../i18n";


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
  const [domains] = useState([]);


  return (
    <div className="admin">
      <h2 className="section-title">{t("admin.title")}</h2>
      <p className="section-intro">{t("admin.intro")}</p>

           <div className="kpi-grid">
        <div className="kpi"><span>{t("admin.totalChecks")}</span><strong>—</strong></div>
        <div className="kpi"><span>{t("admin.highRisk")}</span><strong>—</strong></div>
        <div className="kpi"><span>{t("admin.activePatterns")}</span><strong>—</strong></div>
      </div>

      <h3>{t("admin.checksPerDay")}</h3>
      <p className="section-intro">{t("admin.checksPerDayWaiting")}</p>

      <h3>{t("admin.scamTypes")}</h3>
      <div className="pie">
              <p className="section-intro">{t("admin.noData")}</p>
      </div>

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