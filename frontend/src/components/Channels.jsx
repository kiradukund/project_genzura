import { useI18n } from "../i18n";

// The three ways to use Genzura from the feature spec. USSD and SMS are
// still being built (Abay), so they are marked "Coming soon".
const CHANNELS = [
  {
    id: "web",
    live: true,
    icon: "M3 5h18v12H3z M8 21h8 M12 17v4",
  },
  {
    id: "ussd",
    live: false,
    icon: "M7 2h10v20H7z M10 18h4 M10 6h1 M13 6h1 M10 9h1 M13 9h1 M10 12h1 M13 12h1",
  },
  {
    id: "sms",
    live: false,
    icon: "M4 4h16v12H8l-4 4z M8 9h8 M8 12h5",
  },
];

export default function Channels() {
  const { t } = useI18n();

  return (
    <ul className="channels">
      {CHANNELS.map((c) => (
        <li key={c.id} className="channel">
          <div className="channel-top">
            <svg viewBox="0 0 24 24" aria-hidden="true" className="channel-icon">
              <path d={c.icon} fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            <span className={`pill ${c.live ? "live" : ""}`}>
              {c.live ? t("channels.available") : t("channels.soon")}
            </span>
          </div>
          <h3>{t(`channels.${c.id}.title`)}</h3>
          <p>{t(`channels.${c.id}.body`)}</p>
        </li>
      ))}
    </ul>
  );
}
