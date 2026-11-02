import heroPerson from "../assets/hero-person.webp";
import heroPersonSm from "../assets/hero-person-sm.webp";
import BackToTop from "../components/BackToTop";
import Channels from "../components/Channels";
import Faq from "../components/Faq";
import Footer from "../components/Footer";
import Header from "../components/Header";
import { useI18n } from "../i18n";
import useReveal from "../useReveal";
import Checker from "./Checker";
import Directory from "./Directory";

const STEPS = ["1", "2", "3"];

// Scam signs the API can flag (labels live in i18n under "flags").
const SIGNS = [
  "upfront_fee",
  "guaranteed_outcome",
  "urgency_pressure",
  "free_email_contact",
  "chat_app_only",
  "sensitive_info_request",
  "blacklisted_entity",
  "flagged_entity",
];

export default function Home() {
  const { t } = useI18n();
  useReveal();

  return (
    <>
      <Header />
      <main id="top">
        <section className="hero">
          <div className="hero-wrap">
            <div className="hero-inner">
              <h1>{t("title")}</h1>
              <p className="hero-sub">{t("subtitle")}</p>
              <div className="hero-actions">
                <a className="btn-primary" href="#check">
                  {t("home.cta")}
                </a>
                <a className="btn-ghost" href="#how">
                  {t("home.stepsTitle")}
                </a>
              </div>
              <p className="hero-trust">{t("home.trust")}</p>
            </div>

            <div className="hero-visual" aria-hidden="true">
              <div className="hero-orb" />
              <img
                className="hero-person"
                src={heroPerson}
                srcSet={`${heroPersonSm} 292w, ${heroPerson} 540w`}
                sizes="(min-width: 900px) 380px, 220px"
                alt=""
                width="540"
                height="814"
                fetchpriority="high"
                decoding="async"
              />
              {/* Decorative preview of a result, shown on wide screens only. */}
              <div className="hero-card">
                <span className="hero-card-badge">{t("risk.high_risk")}</span>
                <span className="hero-card-flag">{t("flags.upfront_fee")}</span>
                <span className="hero-card-flag">{t("flags.guaranteed_outcome")}</span>
              </div>
            </div>
          </div>
        </section>

        <section id="how" className="section reveal" aria-labelledby="steps-title">
          <h2 id="steps-title" className="section-title">
            {t("home.stepsTitle")}
          </h2>
          <ol className="steps">
            {STEPS.map((n) => (
              <li key={n} className="step">
                <span className="step-num" aria-hidden="true">
                  {n}
                </span>
                <h3>{t(`home.steps.${n}.title`)}</h3>
                <p>{t(`home.steps.${n}.body`)}</p>
              </li>
            ))}
          </ol>
        </section>

        <section id="check" className="section check-section" aria-labelledby="check-title">
          <h2 id="check-title" className="section-title">
            {t("home.checkTitle")}
          </h2>
          <div className="check-card">
            <Checker />
          </div>
        </section>

        <section id="channels" className="section reveal" aria-labelledby="channels-title">
          <h2 id="channels-title" className="section-title">
            {t("channels.title")}
          </h2>
          <p className="section-intro">{t("channels.intro")}</p>
          <Channels />
        </section>

        <section id="signs" className="section reveal" aria-labelledby="signs-title">
          <h2 id="signs-title" className="section-title">
            {t("home.signsTitle")}
          </h2>
          <p className="section-intro">{t("home.signsIntro")}</p>
          <ul className="signs">
            {SIGNS.map((id) => (
              <li key={id}>{t(`flags.${id}`)}</li>
            ))}
          </ul>
        </section>

        <section id="directory" className="section reveal">
          <Directory />
        </section>

        <section id="faq" className="section reveal" aria-labelledby="faq-title">
          <h2 id="faq-title" className="section-title">
            {t("faq.title")}
          </h2>
          <Faq />
        </section>

        <section id="report" className="section reveal">
          <div className="rib-band">
            <div>
              <h2>{t("home.ribTitle")}</h2>
              <p>{t("home.ribBody")}</p>
            </div>
            <a className="btn-danger" href="tel:166">
              {t("actions.reportRib")}
            </a>
          </div>
        </section>
      </main>
      <Footer />
      <BackToTop />
    </>
  );
}
