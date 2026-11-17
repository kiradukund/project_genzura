// OWNER: Kuol - Privacy page (/privacy)
import { useI18n } from "../i18n";

// Same order as the "privacy.sections" block in en.json / rw.json.
const SECTIONS = ["checks", "links", "account", "alerts", "channels", "reports", "where", "rights"];

export default function Privacy() {
  const { t } = useI18n();

  return (
    <main id="top" className="section page privacy">
      <h1 className="section-title">{t("privacy.title")}</h1>
      <p className="section-intro">{t("privacy.intro")}</p>

      <ol className="privacy-list">
        {SECTIONS.map((id) => (
          <li key={id}>
            <h2>{t(`privacy.sections.${id}.title`)}</h2>
            <p>{t(`privacy.sections.${id}.body`)}</p>
          </li>
        ))}
      </ol>

      <p className="privacy-updated">{t("privacy.updated")}</p>
    </main>
  );
}
