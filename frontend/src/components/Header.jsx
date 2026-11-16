// OWNER: Kuol - Top bar and menu
import { useEffect, useState } from "react";
import logo from "../assets/logo.png";
import { useI18n } from "../i18n";
import { Link, useLocation } from "../router";
import LanguageMenu from "./LanguageMenu";

// Links to sections of the home page. They work from any page.
const NAV = [
  { id: "how", key: "nav.how" },
  // On wide screens "Check an offer" is the red button on the right instead.
  { id: "check", key: "nav.check", mobileOnly: true },
  { id: "signs", key: "nav.signs" },
  { id: "already-paid", key: "nav.alreadyPaid" },
];

// Links to separate pages. Add one when its route is turned on in App.jsx,
// and add its label to the "nav" block in en.json.
const PAGE_LINKS = [
  { to: "/directory", key: "nav.directory" },
  // { to: "/assess", key: "nav.assess" },
  // { to: "/trends", key: "nav.trends" },
  // { to: "/agencies", key: "nav.agencies" },
  // { to: "/my-checks", key: "nav.myChecks" },
  // { to: "/signin", key: "nav.signIn" },
];

// Highlight the menu link for the section currently on screen.
function useActiveSection(ids, path) {
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
  }, [ids, path]);

  return active;
}

const NAV_IDS = NAV.map((item) => item.id);

// Top bar: brand, menu and language switch. Stays visible while scrolling.
export default function Header() {
  const { t } = useI18n();
  const [open, setOpen] = useState(false);
  const { path } = useLocation();
  const onHome = path === "/";
  const active = useActiveSection(NAV_IDS, path);
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
        <Link className="brand" to="/#top" onClick={() => setOpen(false)}>
          <img className="logo" src={logo} alt={t("appName")} width="457" height="362" />
        </Link>

        <nav id="site-nav" className={`nav ${open ? "open" : ""}`} aria-label={t("nav.label")}>
          <ul>
            {NAV.map((item) => {
              const isActive = onHome && active === item.id;
              return (
                <li key={item.id} className={item.mobileOnly ? "mobile-only" : undefined}>
                  <Link
                    to={`/#${item.id}`}
                    className={isActive ? "active" : ""}
                    aria-current={isActive ? "location" : undefined}
                    onClick={() => setOpen(false)}
                  >
                    {t(item.key)}
                  </Link>
                </li>
              );
            })}
            {PAGE_LINKS.map((item) => (
              <li key={item.to}>
                <Link
                  to={item.to}
                  className={path === item.to ? "active" : ""}
                  aria-current={path === item.to ? "page" : undefined}
                  onClick={() => setOpen(false)}
                >
                  {t(item.key)}
                </Link>
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

        <Link className="topbar-cta" to="/#check" onClick={() => setOpen(false)}>
          {t("nav.check")}
        </Link>
      </div>
    </header>
  );
}
