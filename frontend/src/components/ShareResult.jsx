import { useState } from "react";
import { useI18n } from "../i18n";

// Lets people warn friends and family. Only the verdict and red flags are
// shared, never the offer text itself (it may contain personal details).
export default function ShareResult({ verdict, flagLabels }) {
  const { t } = useI18n();
  const [copied, setCopied] = useState(false);

  const message = [
    `${t("share.intro")} ${t(`risk.${verdict}`)}.`,
    flagLabels.length ? `${t("share.flags")} ${flagLabels.join(", ")}.` : "",
    `${t("share.outro")} ${window.location.origin}`,
  ]
    .filter(Boolean)
    .join("\n");

  async function copy() {
    try {
      await navigator.clipboard.writeText(message);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard blocked (e.g. non-HTTPS): nothing else to do.
    }
  }

  return (
    <div className="share">
      <a
        className="btn-share whatsapp"
        href={`https://wa.me/?text=${encodeURIComponent(message)}`}
        target="_blank"
        rel="noopener noreferrer"
      >
        <svg viewBox="0 0 24 24" aria-hidden="true" className="icon">
          <path
            fill="currentColor"
            d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2zm0 18.2a8.2 8.2 0 0 1-4.2-1.2l-.3-.2-3 .8.8-2.9-.2-.3A8.2 8.2 0 1 1 12 20.2zm4.5-6.1c-.2-.1-1.5-.7-1.7-.8-.2-.1-.4-.1-.6.1l-.8 1c-.1.2-.3.2-.5.1a6.7 6.7 0 0 1-3.3-2.9c-.2-.4.2-.4.7-1.3.1-.2 0-.3 0-.4l-.8-1.8c-.2-.5-.4-.4-.6-.4h-.5a1 1 0 0 0-.7.3 2.9 2.9 0 0 0-.9 2.2 5 5 0 0 0 1.1 2.7 11.5 11.5 0 0 0 4.4 3.9c1.6.7 2.3.8 3.1.6a2.6 2.6 0 0 0 1.7-1.2 2.1 2.1 0 0 0 .2-1.2c-.1-.1-.3-.2-.5-.3z"
          />
        </svg>
        {t("share.whatsapp")}
      </a>
      <button type="button" className="btn-share" onClick={copy}>
        <svg viewBox="0 0 24 24" aria-hidden="true" className="icon">
          <path
            d={copied ? "M5 12l5 5 9-10" : "M8 8h11v13H8z M5 16V3h11"}
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinejoin="round"
          />
        </svg>
        <span aria-live="polite">{copied ? t("share.copied") : t("share.copy")}</span>
      </button>
    </div>
  );
}
