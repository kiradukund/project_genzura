import { useI18n } from "../i18n";

// Call RIB on 166. The "Find a Digital Ambassador" button was removed until
// there is a real ambassador contact list to show.
export default function ActionButtons() {
  const { t } = useI18n();

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
    </div>
  );
}
