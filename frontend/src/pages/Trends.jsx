// OWNER: Alier - Trending scams page
import "./Trends.css";
import { useEffect, useState } from "react";
import { getTrends } from "../api/trends";
import { useI18n } from "../i18n";

const PERIODS = [7, 30];

function humanize(id) {
  const words = String(id).replace(/_/g, " ").toLowerCase();
  return words.charAt(0).toUpperCase() + words.slice(1);
}

// A list of bars: label, count, and a bar sized against the largest count.
function BarList({ items, label }) {
  const max = Math.max(...items.map((i) => i.count), 1);
  return (
    <ul className="trends-bars">
      {items.map((item) => (
        <li key={item.id}>
          <div className="trends-bar-label">
            <span>{label(item.id)}</span>
            <strong>{item.count}</strong>
          </div>
          <div className="trends-bar" aria-hidden="true">
            <div style={{ width: `${(item.count / max) * 100}%` }} />
          </div>
        </li>
      ))}
    </ul>
  );
}

export default function Trends() {
  const { t, has } = useI18n();
  const [days, setDays] = useState(7);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(false);
    getTrends(days)
      .then((body) => !cancelled && setData(body))
      .catch(() => !cancelled && setError(true))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [days]);

  const flagLabel = (id) => (has(`flags.${id}`) ? t(`flags.${id}`) : humanize(id));
  const typeLabel = (id) => (has(`offerType.${id}`) ? t(`offerType.${id}`) : humanize(id));

  return (
    <div className="trends">
      <h2 className="section-title">{t("trends.title")}</h2>
      <p className="section-intro">{t("trends.intro")}</p>

      <div className="toggle" role="radiogroup" aria-label={t("trends.period")}>
        {PERIODS.map((p) => (
          <button
            key={p}
            type="button"
            role="radio"
            aria-checked={days === p}
            className={days === p ? "active" : ""}
            onClick={() => setDays(p)}
          >
            {t(`trends.last${p}`)}
          </button>
        ))}
      </div>

      {loading && <p className="muted">{t("trends.loading")}</p>}
      {!loading && error && (
        <p className="trends-error" role="alert">
          {t("trends.error")}
        </p>
      )}

      {!loading && !error && data && (
        <div aria-live="polite">
          <p className="trends-based-on">{t("trends.basedOn").replace("{n}", data.total)}</p>

          {!data.enough_data ? (
            <p className="trends-empty">{t("trends.notEnough")}</p>
          ) : (
            <>
              <h3>{t("trends.flagsTitle")}</h3>
              {data.flags.length === 0 ? (
                <p className="muted">{t("trends.noneYet")}</p>
              ) : (
                <BarList items={data.flags} label={flagLabel} />
              )}

              <h3>{t("trends.typesTitle")}</h3>
              {data.contexts.length === 0 ? (
                <p className="muted">{t("trends.noneYet")}</p>
              ) : (
                <BarList items={data.contexts} label={typeLabel} />
              )}
            </>
          )}

          <p className="trends-privacy muted">{t("trends.privacy")}</p>
        </div>
      )}
    </div>
  );
}
