// OWNER: Chol - Report a scam form
import { useState } from "react";
import { useI18n } from "../i18n";
import { submitReport } from "../api/reports";

export default function ReportForm({ checkId }) {
  const { t } = useI18n();
  const [text, setText] = useState("");
  const [contact, setContact] = useState("");
  const [status, setStatus] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    setStatus("sending");
    try {
      await submitReport({ text, contact, check_id: checkId });
      setStatus("done");
    } catch {
      setStatus("error");
    }
  }

  if (status === "done") return <p>{t("report.done")}</p>;

  return (
    <form onSubmit={handleSubmit}>
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder={t("report.placeholder")}
        required
        rows={4}
      />
      <input
        value={contact}
        onChange={(e) => setContact(e.target.value)}
        placeholder={t("report.contactPlaceholder")}
      />
      <button type="submit" disabled={status === "sending"}>
        {status === "sending" ? t("report.submitting") : t("report.submit")}
      </button>
      {status === "error" && <p>{t("report.error")}</p>}
    </form>
  );
}
