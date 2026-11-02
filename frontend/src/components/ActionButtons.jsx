import { useState } from "react";
import { useI18n } from "../i18n";

// No ambassador data source yet: the schema has no ambassador table and Kevin
// must confirm the data source and privacy rules first. Fill this list (or swap
// it for an API call) once that is decided. Shape: { name, area, phone }.
const AMBASSADORS = [];

export default function ActionButtons() {
  const { t } = useI18n();
  const [showAmbassadors, setShowAmbassadors] = useState(false);

  return (
    <div className="actions">
      <a className="btn-danger" href="tel:166">
        <svg viewBox="0 0 24 24" aria-hidden="true" className="icon">
          <path
            d="M5 3h4l2 5-2.5 1.5a11 11 0 0 0 6 6L16 13l5 2v4a2 2 0 0 1-2 2A17 17 0 0 1 3 5a2 2 0 0 1 2-2z"
            fill="currentColor"
          />
        </svg>
        {t("actions.reportRib")}
      </a>
      <button
        type="button"
        className="btn-outline"
        aria-expanded={showAmbassadors}
        onClick={() => setShowAmbassadors((v) => !v)}
      >
        {t("actions.findAmbassador")}
      </button>

      {showAmbassadors && (
        <div className="panel">
          <h3>{t("actions.ambassadorTitle")}</h3>
          {AMBASSADORS.length === 0 ? (
            <p>{t("actions.ambassadorEmpty")}</p>
          ) : (
            <ul className="ambassadors">
              {AMBASSADORS.map((a) => (
                <li key={`${a.name}-${a.area}`}>
                  <strong>{a.name}</strong> <span>{a.area}</span>
                  {a.phone && <a href={`tel:${a.phone}`}>{a.phone}</a>}
                </li>
              ))}
            </ul>
          )}
          <button type="button" className="link" onClick={() => setShowAmbassadors(false)}>
            {t("actions.close")}
          </button>
        </div>
      )}
    </div>
  );
}
