import "leaflet/dist/leaflet.css";
import "./Admin.css";
import { useState } from "react";
import { Pie } from "react-chartjs-2";
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from "chart.js";
import { sampleKpis, sampleModus } from "../data/adminSample.js";
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
   const [domains] = useState([]);

  const pieData = {
    labels: sampleModus.map((m) => m.label),
    datasets: [
      {
        data: sampleModus.map((m) => m.value),
                backgroundColor: ["#d4af37", "#f5f1e6", "#8a9bb5"],
      },
    ],
  };

  return (
    <div className="admin">
      <h2 className="section-title">Admin intelligence dashboard</h2>
      <p className="section-intro">Sample data. Real figures appear when the admin API is ready.</p>

      <div className="kpi-grid">
        <div className="kpi"><span>Total checks</span><strong>{sampleKpis.totalChecks.toLocaleString()}</strong></div>
        <div className="kpi"><span>High-risk</span><strong>{sampleKpis.highRisk}</strong></div>
        
        <div className="kpi"><span>Active patterns</span><strong>{sampleKpis.activePatterns}</strong></div>
      </div>

            <h3>Checks per day</h3>
      <p className="section-intro">Waiting for live data. This chart appears when the admin stats are connected.</p>

      <h3>Scam types</h3>
      <div className="pie">
        <Pie data={pieData} />
      </div>
      <h3>Trending domains</h3>
      {domains.length === 0 ? (
        <p className="section-intro">No data yet.</p>
      ) : (
        <>
          <button type="button" onClick={() => downloadCsv(domains)}>Download CSV</button>
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
