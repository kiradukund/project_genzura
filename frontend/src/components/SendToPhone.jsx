import { useState } from "react";
import { sendResultSms } from "../api/client";
import { useI18n } from "../i18n";

// Rwandan mobile: 07X XXX XXXX or +250 7X XXX XXXX
const RW_PHONE = /^(\+?250|0)7[2389]\d{7}$/;

export default function SendToPhone({ checkId }) {
  const { t, lang } = useI18n();
  const [phone, setPhone] = useState("");
  const [status, setStatus] = useState("idle"); // idle | sending | sent | error
  const [message, setMessage] = useState("");

  async function submit(e) {
    e.preventDefault();
    const cleaned = phone.replace(/[\s-]/g, "");
    if (!RW_PHONE.test(cleaned)) {
      setStatus("error");
      setMessage(t("sms.invalid"));
      return;
    }
    setStatus("sending");
    try {
      await sendResultSms({ phone: cleaned, checkId, language: lang });
      setStatus("sent");
      setMessage(t("sms.sent"));
    } catch {
      setStatus("error");
      setMessage(t("sms.failed"));
    }
  }

  return (
    <form className="sms-form" onSubmit={submit}>
      <label htmlFor="sms-phone">{t("sms.label")}</label>
      <div className="sms-row">
        <input
          id="sms-phone"
          type="tel"
          inputMode="tel"
          autoComplete="tel"
          placeholder={t("sms.placeholder")}
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
        />
        <button type="submit" className="btn-primary" disabled={status === "sending" || !phone.trim()}>
          {status === "sending" ? t("sms.sending") : t("sms.send")}
        </button>
      </div>
      {message && (
        <p className={status === "sent" ? "success" : "error"} role="status">
          {message}
        </p>
      )}
    </form>
  );
}
