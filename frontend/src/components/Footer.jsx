import logo from "../assets/logo.png";
import { useI18n } from "../i18n";
import { Link } from "../router";

const LINKS = [
  { href: "/#how", key: "nav.how" },
  { href: "/#check", key: "nav.check" },
  { href: "/#signs", key: "nav.signs" },
  { href: "/#already-paid", key: "nav.alreadyPaid" },
  { href: "/#faq", key: "footer.faq" },
];

export default function Footer() {
  const { t } = useI18n();
  const year = new Date().getFullYear();

  return (
    <footer className="footer">
      <div className="footer-inner">
        <div className="footer-brand">
          <img className="footer-logo" src={logo} alt={t("appName")} width="457" height="362" loading="lazy" />
          <p>{t("footer.tagline")}</p>
        </div>

        <nav aria-label={t("footer.explore")}>
          <h3>{t("footer.explore")}</h3>
          <ul>
            {LINKS.map((l) => (
              <li key={l.href}>
                <Link to={l.href}>{t(l.key)}</Link>
              </li>
            ))}
          </ul>
        </nav>

        <div>
          <h3>{t("footer.help")}</h3>
          <a className="footer-call" href="tel:166">
            <strong>166</strong>
            <span>{t("footer.rib")}</span>
          </a>
          <p className="footer-privacy">{t("footer.privacy")}</p>
        </div>
      </div>

      <div className="footer-bottom">
        <span>
          © {year} {t("appName")}. {t("footer.rights")}
        </span>
        <span>{t("footer.made")}</span>
      </div>
    </footer>
  );
}
