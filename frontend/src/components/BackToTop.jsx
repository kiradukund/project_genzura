import { useEffect, useState } from "react";
import { useI18n } from "../i18n";

// Floating button that appears after scrolling down a screen or so.
export default function BackToTop() {
  const { t } = useI18n();
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const onScroll = () => setVisible(window.scrollY > 700);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <a href="#top" className={`to-top ${visible ? "show" : ""}`} aria-label={t("footer.top")} tabIndex={visible ? 0 : -1}>
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M6 15l6-6 6 6" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </a>
  );
}
