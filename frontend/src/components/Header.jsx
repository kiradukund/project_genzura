import { useEffect, useState } from "react";
import logo from "../assets/logo.png";
import { useI18n } from "../i18n";
import LanguageMenu from "./LanguageMenu";

// Menu links jump to sections of the home page. When the site gets real pages
// (Directory, etc.), add them here.
const NAV = [
  { id: "how", key: "nav.how" },
  { id: "check", key: "nav.check" },
  { id: "signs", key: "nav.signs" },
  { id: "report", key: "nav.report" },
];

// Highlight the menu link for the section currently on screen.
function useActiveSection(ids) {
  const [active, setActive] = useState("");

  useEffect(() => {
    if (!("IntersectionObserver" in window)) return undefined;
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) setActive(entry.target.id);
        });
      },
      { rootMargin: "-45% 0px -50% 0px" },
    );
    ids.forEach((id) => {
      const el = document.getElementById(id);
      if (el) observer.observe(el);
    });
    return () => observer.disconnect();
  }, [ids]);

  return active;
}

const NAV_IDS = NAV.map((item) => item.id);

// Top bar: brand, menu and language switch. Stays visible while scrolling.
export default function Header() {
  const { t } = useI18n();
  const [open, setOpen] = useState(false);
  const active = useActiveSection(NAV_IDS);
  const [scrolled, setScrolled] = useState(false);

  // Add a shadow to the bar once the page is scrolled.
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  // Close the phone menu with the Escape key.
  useEffect(() => {
    if (!open) return undefined;
    const onKey = (e) => e.key === "Escape" && setOpen(false);
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  return (
    <header className={`topbar ${scrolled ? "scrolled" : ""}`}>
      <div className="topbar-inner">
        <a className="brand" href="#top" onClick={() => setOpen(false)}>
          <img className="logo" src={logo} alt={t("appName")} width="240" height="188" />
        </a>

        <nav id="site-nav" className={`nav ${open ? "open" : ""}`} aria-label={t("nav.label")}>
          <ul>
            {NAV.map((item) => (
              <li key={item.id}>
                <a
                  href={`#${item.id}`}
                  className={active === item.id ? "active" : ""}
                  aria-current={active === item.id ? "location" : undefined}
                  onClick={() => setOpen(false)}
                >
                  {t(item.key)}
                </a>
              </li>
            ))}
          </ul>
        </nav>

        <div className="topbar-right">
          <LanguageMenu />
          <button
            type="button"
            className="menu-btn"
            aria-expanded={open}
            aria-controls="site-nav"
            aria-label={t("nav.menu")}
            onClick={() => setOpen((v) => !v)}
          >
            <svg viewBox="0 0 24 24" aria-hidden="true">
              {open ? (
                <path d="M6 6l12 12M18 6L6 18" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
              ) : (
                <path d="M4 7h16M4 12h16M4 17h16" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
              )}
            </svg>
          </button>
        </div>
      </div>
    </header>
  );
}
