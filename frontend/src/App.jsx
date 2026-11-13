// OWNER: Kuol - App shell and page routes
import BackToTop from "./components/BackToTop";
import Footer from "./components/Footer";
import Header from "./components/Header";
import { I18nProvider, useI18n } from "./i18n";
import Directory from "./pages/Directory";
import Home from "./pages/Home";
import { RouterProvider, useLocation } from "./router";
// Import each page here when its owner says it is ready:
import Assess from "./pages/Assess";
// import Trends from "./pages/Trends";
// import Agencies from "./pages/Agencies";
// import SignIn from "./pages/SignIn";
// import MyChecks from "./pages/MyChecks";
// import Admin from "./pages/Admin";

// Pages from other files are wrapped so every page has the same <main> frame.
function DirectoryPage() {
  return (
    <main id="top" className="section page">
      <Directory />
    </main>
  );
}

function AssessPage() {
  return (
    <main id="top" className="section page">
      <Assess />
    </main>
  );
}

// One line per page. To plug in a finished page:
//   1. uncomment its import above and its line below
//   2. add its menu link in components/Header.jsx (PAGE_LINKS)
export const ROUTES = {
  "/": Home,
  "/directory": DirectoryPage,
  "/assess": AssessPage,
  // "/trends": Trends,
  // "/agencies": Agencies,
  // "/signin": SignIn,
  // "/my-checks": MyChecks,
  // "/admin": Admin,
};

function NotFound() {
  const { t } = useI18n();
  return (
    <main id="top" className="section page-not-found">
      <h1 className="section-title">{t("nav.notFound")}</h1>
      <a className="btn-primary" href="/">
        {t("nav.home")}
      </a>
    </main>
  );
}

function CurrentPage() {
  const { path } = useLocation();
  // "/trends/" and "/trends" are the same page.
  const clean = path.length > 1 ? path.replace(/\/+$/, "") : path;
  const Page = ROUTES[clean] || NotFound;
  return <Page />;
}

export default function App() {
  return (
    <I18nProvider>
      <RouterProvider>
        <Header />
        <CurrentPage />
        <Footer />
        <BackToTop />
      </RouterProvider>
    </I18nProvider>
  );
}
