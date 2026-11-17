// OWNER: Kuol - App shell and page routes
import { useEffect } from "react";
import { getSession } from "./api/auth";
import BackToTop from "./components/BackToTop";
import Footer from "./components/Footer";
import Header from "./components/Header";
import { I18nProvider, useI18n } from "./i18n";
import Directory from "./pages/Directory";
import Home from "./pages/Home";
import { RouterProvider, navigate, useLocation } from "./router";
// Import each page here when its owner says it is ready:
import Admin from "./pages/Admin";
import Agencies from "./pages/Agencies";
import Assess from "./pages/Assess";
import MyChecks from "./pages/MyChecks";
import Privacy from "./pages/Privacy";
import SignIn from "./pages/SignIn";
import Trends from "./pages/Trends";

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

function AdminPage() {
  return (
    <main id="top" className="section page">
      <Admin />
    </main>
  );
}

function AgenciesPage() {
  return (
    <main id="top" className="page agencies-page">
      <Agencies />
    </main>
  );
}

// After signing in: the team goes to the dashboard, everyone else to their checks.
function goAfterSignIn(session) {
  navigate(session?.kind === "admin" ? "/admin" : "/my-checks");
}

function goToSignIn() {
  navigate("/signin");
}

// SignIn and MyChecks already have their own <main>, so they get a <div> frame.
function SignInPage() {
  const { t } = useI18n();

  // Already signed in? Skip the form.
  useEffect(() => {
    let cancelled = false;
    getSession()
      .then((session) => {
        if (session && !cancelled) goAfterSignIn(session);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div id="top" className="section page">
      <SignIn onSignedIn={goAfterSignIn} />
      {/* For first-time visitors: signing in also creates the account. */}
      <p className="signin-new">{t("signInPage.newHere")}</p>
    </div>
  );
}

function MyChecksPage() {
  return (
    <div id="top" className="section page">
      <MyChecks onSignedOut={goToSignIn} />
    </div>
  );
}

// One line per page. To plug in a finished page:
//   1. uncomment its import above and its line below
//   2. add its menu link in components/Header.jsx (PAGE_LINKS)
export const ROUTES = {
  "/": Home,
  "/directory": DirectoryPage,
  "/assess": AssessPage,
  "/signin": SignInPage,
  "/my-checks": MyChecksPage,
  "/admin": AdminPage,
  "/agencies": AgenciesPage,
  "/privacy": Privacy,
  "/trends": Trends,
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
