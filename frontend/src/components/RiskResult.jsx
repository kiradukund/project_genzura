import { useEffect, useRef } from "react";
import { useI18n } from "../i18n";
import ActionButtons from "./ActionButtons";
import AlreadyPaid from "./AlreadyPaid";
import SendToPhone from "./SendToPhone";
import ShareResult from "./ShareResult";

const SMS_ENABLED = import.meta.env.VITE_ENABLE_SMS_RESULT === "true";

// Flags may come back as ids ("upfront_fee") or objects ({ id, label }).
function flagId(flag) {
  return typeof flag === "string" ? flag : flag.id;
}

function humanize(id) {
  const words = String(id).replace(/_/g, " ").toLowerCase();
  return words.charAt(0).toUpperCase() + words.slice(1);
}

export default function RiskResult({ result }) {
  const { t, has } = useI18n();
  const ref = useRef(null);
  const verdict = result.verdict || "low_risk";
  const flags = result.flags || [];

  // Bring the result into view on small screens.
  useEffect(() => {
    ref.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    ref.current?.focus({ preventScroll: true });
  }, [result]);

  const flagLabel = (flag) => {
    const id = flagId(flag);
    if (has(`flags.${id}`)) return t(`flags.${id}`);
    return flag.label || humanize(id);
  };

  return (
    <section className={`result result-${verdict}`} ref={ref} tabIndex={-1} aria-live="polite">
      <div className="badge">{t(`risk.${verdict}`)}</div>
      <p className="explain">{t(`explain.${verdict}`)}</p>
      {typeof result.risk_score === "number" && (
        <div className="score">
          <span>{t("score")}</span>
          <div className="meter" aria-hidden="true">
            <div style={{ width: `${Math.min(100, result.risk_score)}%` }} />
          </div>
          <strong>{result.risk_score}/100</strong>
        </div>
      )}

      <h2>{t("flagsTitle")}</h2>
      {flags.length === 0 ? (
        <p className="muted">{t("noFlags")}</p>
      ) : (
        <ul className="flags">
          {flags.map((flag) => (
            <li key={flagId(flag)}>{flagLabel(flag)}</li>
          ))}
        </ul>
      )}

      <h2>{t("nextSteps")}</h2>
      <ActionButtons />
      {verdict !== "low_risk" && <AlreadyPaid compact />}
      <ShareResult verdict={verdict} flagLabels={flags.map(flagLabel)} />
      {SMS_ENABLED && <SendToPhone checkId={result.check_id} />}
    </section>
  );
}
