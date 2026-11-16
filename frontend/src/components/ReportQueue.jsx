// OWNER: Didier - Admin review queue for scam reports (uses Chol's api/reports.js)
import { useEffect, useState } from "react";
import { useI18n } from "../i18n";
import { fetchReports, approveReport, rejectReport } from "../api/reports.js";

const TABS = ["pending", "approved", "rejected"];

export default function ReportQueue() {
  const { t } = useI18n();
  const [tab, setTab] = useState("pending");
  const [reports, setReports] = useState([]);
  const [status, setStatus] = useState("loading");
  const [notes, setNotes] = useState({});

  function load(which) {
    setStatus("loading");
    fetchReports(which)
      .then((data) => {
        setReports(data);
        setStatus("ready");
      })
      .catch(() => setStatus("error"));
  }

  useEffect(() => {
    load(tab);
  }, [tab]);

  function decide(id, action) {
    const note = notes[id] || "";
    const call = action === "approve" ? approveReport : rejectReport;
    call(id, note)
      .then(() => setReports((list) => list.filter((r) => r.id !== id)))
      .catch(() => setStatus("error"));
  }

  return (
    <section className="report-queue">
      <h3>{t("admin.reportsTitle")}</h3>

      <div role="tablist">
        {TABS.map((name) => (
          <button
            key={name}
            type="button"
            role="tab"
            aria-selected={tab === name}
            onClick={() => setTab(name)}
          >
            {t(`admin.tab_${name}`)}
          </button>
        ))}
      </div>

      {status === "loading" && <p className="section-intro">{t("admin.loading")}</p>}
      {status === "error" && <p className="section-intro">{t("admin.reportsError")}</p>}
      {status === "ready" && reports.length === 0 && (
        <p className="section-intro">{t("admin.noReports")}</p>
      )}

      {status === "ready" && reports.length > 0 && (
        <table className="domains">
          <thead>
            <tr>
              <th>{t("admin.colMessage")}</th>
              <th>{t("admin.colContact")}</th>
              <th>{t("admin.colReceived")}</th>
              {tab === "pending" && <th>{t("admin.colAction")}</th>}
            </tr>
          </thead>
          <tbody>
            {reports.map((r) => (
              <tr key={r.id}>
                <td>{r.masked_text}</td>
                <td>{r.contact}</td>
                <td>{new Date(r.created_at).toLocaleString()}</td>
                {tab === "pending" && (
                  <td>
                    <input
                      aria-label={t("admin.notePlaceholder")}
                      placeholder={t("admin.notePlaceholder")}
                      value={notes[r.id] || ""}
                      onChange={(e) => setNotes({ ...notes, [r.id]: e.target.value })}
                    />
                    <button type="button" onClick={() => decide(r.id, "approve")}>
                      {t("admin.approve")}
                    </button>
                    <button type="button" onClick={() => decide(r.id, "reject")}>
                      {t("admin.reject")}
                    </button>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
