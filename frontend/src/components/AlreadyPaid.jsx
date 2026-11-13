// OWNER: Kuol - Already paid guide
import { useI18n } from "../i18n";

const RIB = { name: "Rwanda Investigation Bureau (RIB)", url: "https://www.rib.gov.rw" };

// Didier: fill in `phone` for each provider once you have verified the official
// fraud / customer care number (and `url` if a more exact page exists).
// While `phone` is empty, the guide tells people to use the number on the
// provider's official website instead of showing a number we have not checked.
export const PROVIDERS = [
  { id: "mtn", name: "MTN MoMo", phone: "", url: "https://www.mtn.co.rw" },
  { id: "airtel", name: "Airtel Money", phone: "", url: "https://www.airtel.co.rw" },
];

const PHONE_ICON =
  "M5 3h4l2 5-2.5 1.5a11 11 0 0 0 6 6L16 13l5 2v4a2 2 0 0 1-2 2A17 17 0 0 1 3 5a2 2 0 0 1 2-2z";

// Solid white icons drawn on a red tile (24x24). "Cut-outs" use the tile colour.
const CUT = "#c81f35";
const ICONS = {
  // Stop sign
  stop: (
    <>
      <path d="M8 2.5h8l5.5 5.5v8L16 21.5H8L2.5 16V8z" fill="#fff" />
      <rect x="6.5" y="10.4" width="11" height="3.2" rx="1.2" fill={CUT} />
    </>
  ),
  // Receipt with lines
  evidence: (
    <>
      <path d="M5 2.5h14v19l-2.3-1.5-2.4 1.5-2.3-1.5-2.3 1.5-2.4-1.5L5 21.5z" fill="#fff" />
      <rect x="8" y="6.5" width="8" height="1.8" rx="0.9" fill={CUT} />
      <rect x="8" y="10.3" width="8" height="1.8" rx="0.9" fill={CUT} />
      <rect x="8" y="14.1" width="5" height="1.8" rx="0.9" fill={CUT} />
    </>
  ),
  // Phone handset
  rib: <path d={PHONE_ICON} fill="#fff" />,
  // Mobile phone with money on screen
  provider: (
    <>
      <rect x="6" y="1.5" width="12" height="21" rx="2.6" fill="#fff" />
      <rect x="8" y="4" width="8" height="13.5" rx="1" fill={CUT} />
      <rect x="9.2" y="8.2" width="5.6" height="4.6" rx="0.8" fill="#fff" />
      <circle cx="12" cy="10.5" r="1.1" fill={CUT} />
      <circle cx="12" cy="19.9" r="1" fill={CUT} />
    </>
  ),
};

// Every step names the official source it comes from.
const STEPS = [
  { id: "stop", sources: [RIB] },
  { id: "evidence", sources: [RIB] },
  { id: "rib", sources: [RIB], call: "166", urgent: true },
  { id: "provider", sources: PROVIDERS, providers: true },
];

function telHref(phone) {
  return `tel:${phone.replace(/[^\d+]/g, "")}`;
}

function Steps() {
  const { t } = useI18n();

  return (
    <ol className="paid-steps">
      {STEPS.map((step, i) => (
        <li key={step.id} className={`paid-step${step.urgent ? " paid-step-urgent" : ""}`}>
          <div className="paid-step-head">
            <span className="paid-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24">{ICONS[step.id]}</svg>
            </span>
            <span className="paid-num">
              {t("alreadyPaid.step")} {i + 1}
            </span>
          </div>

          <div className="paid-step-body">
            <h3>{t(`alreadyPaid.steps.${step.id}.title`)}</h3>
            <p>{t(`alreadyPaid.steps.${step.id}.body`)}</p>

            {step.call && (
              <a className="btn-danger" href={telHref(step.call)}>
                <svg viewBox="0 0 24 24" aria-hidden="true" className="icon">
                  <path d={PHONE_ICON} fill="currentColor" />
                </svg>
                {t("alreadyPaid.callRib")}
              </a>
            )}

            {step.providers && (
              <ul className="paid-providers">
                {PROVIDERS.map((p) => (
                  <li key={p.id}>
                    <strong>{p.name}</strong>
                    {p.phone ? (
                      <a href={telHref(p.phone)}>{p.phone}</a>
                    ) : (
                      <span className="muted">{t("alreadyPaid.numberOnSite")}</span>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </div>

          <p className="paid-source">
            <span>{t("alreadyPaid.source")}</span>
            {step.sources.map((s, n) => (
              <span key={s.url}>
                <a href={s.url} target="_blank" rel="noopener noreferrer">
                  {s.name}
                </a>
                {n < step.sources.length - 1 && ","}
              </span>
            ))}
          </p>
        </li>
      ))}
    </ol>
  );
}

// Full guide for the home page, or a fold-out box under a risky result (compact).
export default function AlreadyPaid({ compact = false }) {
  const { t } = useI18n();

  if (compact) {
    return (
      <details className="paid paid-compact">
        <summary>{t("alreadyPaid.title")}</summary>
        <p>{t("alreadyPaid.intro")}</p>
        <Steps />
      </details>
    );
  }

  return (
    <div className="paid">
      <h2 id="already-paid-title" className="section-title">
        {t("alreadyPaid.title")}
      </h2>

      {/* Title panel on the left (repeats the heading), steps as joined columns on the right */}
      <div className="paid-board">
        <div className="paid-panel">
          <p className="paid-panel-title" aria-hidden="true">
            {t("alreadyPaid.title")}
          </p>
          <p>{t("alreadyPaid.intro")}</p>
          <span className="paid-panel-arrow" aria-hidden="true">
            &rarr;
          </span>
        </div>
        <Steps />
      </div>
    </div>
  );
}
