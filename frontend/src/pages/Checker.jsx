import { useState } from "react";
import { checkOffer } from "../api/client";
import OfferForm from "../components/OfferForm";
import OfferTypeToggle, { OFFER_TYPES } from "../components/OfferTypeToggle";
import RiskResult from "../components/RiskResult";
import { useI18n } from "../i18n";

// The checking tool: offer type, form, and result. Shown inside the Home page.
export default function Checker() {
  const { t, lang } = useI18n();
  const [context, setContext] = useState("job");
  const [text, setText] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function submit() {
    setLoading(true);
    setError("");
    try {
      setResult(await checkOffer({ text: text.trim(), context, language: lang }));
    } catch {
      setResult(null);
      setError(t("form.error"));
    } finally {
      setLoading(false);
    }
  }

  // Fill the form with a sample scam so first-time visitors can see how it works.
  function applySample(type) {
    setContext(type);
    setText(t(`samples.text.${type}`));
    setResult(null);
    setError("");
  }

  return (
    <div className="checker">
      <OfferTypeToggle value={context} onChange={setContext} />
      <div className="samples">
        <span>{t("samples.label")}</span>
        {OFFER_TYPES.map((type) => (
          <button key={type} type="button" className="chip" onClick={() => applySample(type)}>
            {t(`samples.${type}`)}
          </button>
        ))}
      </div>
      <OfferForm text={text} onTextChange={setText} onSubmit={submit} loading={loading} error={error} />
      {result && <RiskResult result={result} />}
    </div>
  );
}
