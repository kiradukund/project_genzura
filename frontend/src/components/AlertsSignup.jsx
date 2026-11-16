// OWNER: Kuol - Subscribe to scam alerts
import { useState } from "react";
import { subscribeAlerts } from "../api/alerts";
import { useI18n } from "../i18n";

// Rwandan mobile: 07X XXX XXXX or +250 7X XXX XXXX (same rule as the backend)
const RW_PHONE = /^(\+?250|0)7[2389]\d{7}$/;

export default function AlertsSignup() {
  const { t, lang } = useI18n();
  const [phone, setPhone] = useState("");
  const [consent, setConsent] = useState(false);
  const [status, setStatus] = useState("idle"); // idle | sending | done | error
  const [message, setMessage] = useState("");

  async function submit(e) {
    e.preventDefault();
    const cleaned = phone.replace(/[\s-]/g, "");
    if (!RW_PHONE.test(cleaned)) {
      setStatus("error");
      setMessage(t("alerts.invalid"));
      return;
    }
    setStatus("sending");
    try {
      await subscribeAlerts({ phone: cleaned, language: lang });
      setStatus("done");
      setMessage(t("alerts.done"));
      setPhone("");
      setConsent(false);
    } catch {
      setStatus("error");
      setMessage(t("alerts.failed"));
    }
  }

  return (
    <form className="alerts-card" onSubmit={submit}>
      <h2 id="alerts-title" className="section-title">
        {t("alerts.title")}
      </h2>
      <p className="section-intro">{t("alerts.intro")}</p>

      <div className="sms-form">
        <label htmlFor="alerts-phone">{t("alerts.label")}</label>
        <div className="sms-row">
          <input
            id="alerts-phone"
            type="tel"
            inputMode="tel"
            autoComplete="tel"
            placeholder={t("sms.placeholder")}
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
          />
          <button
            type="submit"
            className="btn-primary"
            disabled={status === "sending" || !phone.trim() || !consent}
          >
            {status === "sending" ? t("alerts.sending") : t("alerts.submit")}
          </button>
        </div>
        <label className="alerts-consent">
          <input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} />
          <span>{t("alerts.consent")}</span>
        </label>
      </div>

      {message && (
        <p className={status === "done" ? "success" : "error"} role="status">
          {message}
        </p>
      )}
    </form>
  );
}
