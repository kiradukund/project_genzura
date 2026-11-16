// OWNER: Kuol - Hero demo: a fake scam offer being checked
import { useEffect, useState } from "react";
import { useI18n } from "../i18n";

// The message, split into plain text and red-flag phrases.
// Each flag phrase lights up in turn, then the HIGH RISK stamp lands.
const PARTS = [
  { key: "p1" },
  { key: "f1", flag: "guaranteed_outcome" },
  { key: "p2" },
  { key: "f2", flag: "upfront_fee" },
  { key: "p3" },
  { key: "f3", flag: "urgency_pressure" },
  { key: "p4" },
  { key: "f4", flag: "chat_app_only" },
  { key: "p5" },
];
const FLAGS = PARTS.filter((p) => p.flag);
const LAST = FLAGS.length + 1; // one extra step for the stamp

const STEP_MS = 1100;
const HOLD_MS = 3600;

function prefersReducedMotion() {
  return typeof window !== "undefined" && window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
}

export default function HeroDemo() {
  const { t } = useI18n();
  const [reduced] = useState(prefersReducedMotion);
  const [step, setStep] = useState(reduced ? LAST : 0);

  useEffect(() => {
    if (reduced) return undefined;
    const delay = step === 0 ? 900 : step >= LAST ? HOLD_MS : STEP_MS;
    const id = setTimeout(() => setStep((s) => (s >= LAST ? 0 : s + 1)), delay);
    return () => clearTimeout(id);
  }, [step, reduced]);

  let flagIndex = 0;
  const shown = Math.min(step, FLAGS.length);
  const stamped = step >= LAST;

  return (
    <figure className="demo">
      <div className="demo-phone" aria-hidden="true">
        <div className="demo-head">
          <span className="demo-avatar">A</span>
          <span>
            <strong>{t("home.demo.sender")}</strong>
            <small>{t("home.demo.status")}</small>
          </span>
        </div>

        <div className="demo-chat">
          <p className="demo-bubble">
            {PARTS.map((part) => {
              if (!part.flag) return <span key={part.key}>{t(`home.demo.${part.key}`)}</span>;
              const on = flagIndex++ < shown;
              return (
                <mark key={part.key} className={on ? "on" : ""}>
                  {t(`home.demo.${part.key}`)}
                </mark>
              );
            })}
            <span className="demo-time">09:41</span>
          </p>
        </div>

        <div className="demo-result">
          <ul className="demo-chips">
            {FLAGS.map((f, i) => (
              <li key={f.flag} className={i < shown ? "on" : ""}>
                {t(`flags.${f.flag}`)}
              </li>
            ))}
          </ul>
          <div className="demo-meter">
            <span style={{ left: `${10 + (shown / FLAGS.length) * 80}%` }} />
          </div>
        </div>

        <div className={`demo-stamp${stamped ? " on" : ""}`}>{t("risk.high_risk")}</div>
      </div>
      <figcaption className="sr-only">{t("home.demo.label")}</figcaption>
    </figure>
  );
}
