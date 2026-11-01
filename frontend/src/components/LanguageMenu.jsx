import { useEffect, useRef, useState } from "react";
import { LANGUAGES, useI18n } from "../i18n";

// Each language is always shown in its own name, so people can find theirs
// whichever language the page is currently in.
const NAMES = { en: "English", rw: "Kinyarwanda" };

function Globe() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" strokeWidth="1.8" />
      <path
        d="M3 12h18M12 3c2.5 2.6 3.8 5.6 3.8 9s-1.3 6.4-3.8 9c-2.5-2.6-3.8-5.6-3.8-9S9.5 5.6 12 3z"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinejoin="round"
      />
    </svg>
  );
}

// Globe button with the current language; opens a small list to pick another.
export default function LanguageMenu() {
  const { lang, setLang, t } = useI18n();
  const [open, setOpen] = useState(false);
  const rootRef = useRef(null);

  // Close when clicking elsewhere or pressing Escape.
  useEffect(() => {
    if (!open) return undefined;
    const onClick = (e) => {
      if (rootRef.current && !rootRef.current.contains(e.target)) setOpen(false);
    };
    const onKey = (e) => e.key === "Escape" && setOpen(false);
    document.addEventListener("mousedown", onClick);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onClick);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  function choose(code) {
    setLang(code);
    setOpen(false);
  }

  return (
    <div className="lang-menu" ref={rootRef}>
      <button
        type="button"
        className="lang-trigger"
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label={`${t("language")}: ${NAMES[lang]}`}
        onClick={() => setOpen((v) => !v)}
      >
        <span className="lang-globe">
          <Globe />
        </span>
        <span className="lang-name">{NAMES[lang]}</span>
        <span className="lang-code" aria-hidden="true">
          {lang.toUpperCase()}
        </span>
        <svg className="lang-chevron" viewBox="0 0 24 24" aria-hidden="true">
          <path d="M6 9l6 6 6-6" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </button>

      {open && (
        <ul className="lang-list" role="menu">
          {LANGUAGES.map((code) => (
            <li key={code} role="none">
              <button
                type="button"
                role="menuitemradio"
                aria-checked={code === lang}
                lang={code}
                className={code === lang ? "active" : ""}
                onClick={() => choose(code)}
              >
                {NAMES[code]}
                {code === lang && (
                  <svg viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M5 12l5 5 9-10" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                )}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
