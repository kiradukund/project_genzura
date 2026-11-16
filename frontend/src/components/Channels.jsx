// OWNER: Kuol - Ways to use Genzura (website, USSD, SMS)
import { useI18n } from "../i18n";
// Photos from Pexels (free to use, no credit required: https://www.pexels.com/license/)
//   website: https://www.pexels.com/photo/4560079/
//   ussd:    https://www.pexels.com/photo/14127221/
//   sms:     https://www.pexels.com/photo/9898391/
import smsPhoto from "../assets/channels/sms.jpg";
import ussdPhoto from "../assets/channels/ussd.jpg";
import websitePhoto from "../assets/channels/website.jpg";

// The three ways to use Genzura. USSD and SMS are still being built,
// so they are marked "Coming soon". `focus` picks which part of the photo stays in view.
const CHANNELS = [
  { id: "web", live: true, photo: websitePhoto, focus: "60% 60%" },
  { id: "ussd", live: false, photo: ussdPhoto, focus: "50% 40%" },
  { id: "sms", live: false, photo: smsPhoto, focus: "50% 55%" },
];

export default function Channels() {
  const { t } = useI18n();

  return (
    <ul className="channels">
      {CHANNELS.map(({ id, live, photo, focus }) => (
        <li key={id} className="channel">
          <div className="channel-photo">
            <img src={photo} alt="" loading="lazy" decoding="async" style={{ objectPosition: focus }} />
          </div>
          <div className="channel-body">
            <span className={`pill ${live ? "live" : ""}`}>
              {live ? t("channels.available") : t("channels.soon")}
            </span>
            <h3>{t(`channels.${id}.title`)}</h3>
            <p>{t(`channels.${id}.body`)}</p>
          </div>
        </li>
      ))}
    </ul>
  );
}
