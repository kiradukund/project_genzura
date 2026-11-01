import { useI18n } from "../i18n";

export const OFFER_TYPES = ["job", "scholarship", "visa"];

export default function OfferTypeToggle({ value, onChange }) {
  const { t } = useI18n();

  return (
    <div className="toggle" role="radiogroup" aria-label={t("offerType.label")}>
      {OFFER_TYPES.map((type) => (
        <button
          key={type}
          type="button"
          role="radio"
          aria-checked={value === type}
          className={value === type ? "active" : ""}
          onClick={() => onChange(type)}
        >
          {t(`offerType.${type}`)}
        </button>
      ))}
    </div>
  );
}
