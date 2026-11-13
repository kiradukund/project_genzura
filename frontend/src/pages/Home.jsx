// OWNER: Kuol - Home page
import AlertsSignup from "../components/AlertsSignup";
import AlreadyPaid from "../components/AlreadyPaid";
import Channels from "../components/Channels";
import Faq from "../components/Faq";
import HeroDemo from "../components/HeroDemo";
// Hero photo from Pexels (free to use): https://www.pexels.com/photo/6238088/
import heroBg from "../assets/hero-youth.jpg";
import heroBgSm from "../assets/hero-youth-sm.jpg";
import { directoryEntries } from "../data/directoryEntries";
import { useI18n } from "../i18n";
import { Link } from "../router";
import useReveal from "../useReveal";
import Checker from "./Checker";

// Turn on with VITE_ENABLE_ALERTS=true once SMS and the alerts table are live.
const ALERTS_ENABLED = import.meta.env.VITE_ENABLE_ALERTS === "true";

// The 3 steps use the risk colours: green, amber, red.
const STEPS = [
  { n: "1", tone: "low" },
  { n: "2", tone: "medium" },
  { n: "3", tone: "high" },
];

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
    // Header, Footer and BackToTop are in App.jsx so every page shares them.
    <>
      <main id="top">
        <section className="hero">
          <img
            className="hero-bg"
            src={heroBg}
            srcSet={`${heroBgSm} 900w, ${heroBg} 1920w`}
            sizes="100vw"
            alt=""
            fetchpriority="high"
            decoding="async"
          />
          <div className="hero-wrap">
            <div className="hero-inner">
              <h1>{t("title")}</h1>
              <p className="hero-sub">{t("subtitle")}</p>
              <div className="hero-actions">
                <a className="btn-primary btn-arrow" href="#check">
                  {t("home.cta")}
                </a>
                <a className="btn-ghost btn-arrow" href="#how">
                  {t("home.stepsTitle")}
                </a>
              </div>
            </div>
            {/* What the young person in the photo is reading, checked by Genzura */}
            <HeroDemo />
          </div>
        </section>

        {/* Short promise strip under the hero */}
        <section className="promise" aria-label={t("home.promiseTitle")}>
          <div className="promise-inner">
            <h2>{t("home.promiseTitle")}</h2>
            <p>{t("home.promise")}</p>
            <p className="promise-trust">{t("home.trust")}</p>
          </div>
        </section>

        <section id="how" className="section section-red reveal" aria-labelledby="steps-title">
          <h2 id="steps-title" className="section-title">
            {t("home.stepsTitle")}
          </h2>
          <ol className="steps">
            {STEPS.map(({ n, tone }) => (
              <li key={n} className={`step step-${tone}`}>
                <span className="step-num" aria-hidden="true">
                  {n}
                </span>
                <h3>{t(`home.steps.${n}.title`)}</h3>
                <p>{t(`home.steps.${n}.body`)}</p>
              </li>
            ))}
          </ol>
        </section>

        <section id="check" className="section section-grey check-section" aria-labelledby="check-title">
          <h2 id="check-title" className="section-title">
            {t("home.checkTitle")}
          </h2>
          <div className="check-card">
            <Checker />
          </div>
        </section>

        <section id="signs" className="section reveal" aria-labelledby="signs-title">
          <h2 id="signs-title" className="section-title">
            {t("home.signsTitle")}
          </h2>
          <p className="section-intro">{t("home.signsIntro")}</p>
          <ul className="signs">
            {SIGNS.map((id) => (
              <li key={id}>
                <span className="col-label">{t("home.signLabel")}</span>
                <strong>{t(`flags.${id}`)}</strong>
              </li>
            ))}
          </ul>
        </section>

        <section id="already-paid" className="section reveal" aria-labelledby="already-paid-title">
          <AlreadyPaid />
        </section>

        {/* Short banner; the full list is on its own page (/directory). */}
        <section id="directory" className="section reveal" aria-labelledby="directory-title">
          <div className="band band-navy">
            <div>
              <h2 id="directory-title">{t("directory.title")}</h2>
              <p>{t("directory.intro")}</p>
            </div>
            <Link className="btn-primary btn-arrow" to="/directory">
              {t("home.directoryCta").replace("{n}", directoryEntries.length)}
            </Link>
          </div>
        </section>

        <section id="channels" className="section reveal" aria-labelledby="channels-title">
          <h2 id="channels-title" className="section-title">
            {t("channels.title")}
          </h2>
          <p className="section-intro">{t("channels.intro")}</p>
          <Channels />
        </section>

        {ALERTS_ENABLED && (
          <section id="alerts" className="section reveal" aria-labelledby="alerts-title">
            <AlertsSignup />
          </section>
        )}

        <section id="faq" className="section reveal" aria-labelledby="faq-title">
          <h2 id="faq-title" className="section-title">
            {t("faq.title")}
          </h2>
          <Faq />
        </section>
      </main>
    </>
  );
}
