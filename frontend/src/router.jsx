// OWNER: Kuol - Simple page navigation (no extra library)
//
// Pages use real paths (/trends, /assess...). render.yaml already sends every
// path to index.html, so links and refreshes work in production too.
//
// In a page:
//   import { Link, navigate } from "../router";
//   <Link to="/my-checks">My checks</Link>
//   navigate("/my-checks");          // e.g. after signing in
//   <Link to="/#check">...</Link>     // a section of the home page
import { createContext, useContext, useEffect, useState } from "react";

const RouterContext = createContext({ path: "/", hash: "" });
const EVENT = "genzura:navigate";

function current() {
  return { path: window.location.pathname || "/", hash: window.location.hash };
}

// Change page without reloading the site.
export function navigate(to) {
  const url = new URL(to, window.location.origin);
  const same = url.pathname === window.location.pathname && url.hash === window.location.hash;
  if (!same) window.history.pushState({}, "", url.pathname + url.search + url.hash);
  window.dispatchEvent(new Event(EVENT));
}

export function RouterProvider({ children }) {
  const [location, setLocation] = useState(current);

  useEffect(() => {
    const update = () => setLocation(current());
    window.addEventListener("popstate", update);
    window.addEventListener(EVENT, update);
    return () => {
      window.removeEventListener("popstate", update);
      window.removeEventListener(EVENT, update);
    };
  }, []);

  // After a page change: scroll to the #section if there is one, else to the top.
  useEffect(() => {
    const id = location.hash.slice(1);
    const el = id && document.getElementById(id);
    if (el) el.scrollIntoView();
    else window.scrollTo(0, 0);
  }, [location]);

  return <RouterContext.Provider value={location}>{children}</RouterContext.Provider>;
}

export function useLocation() {
  return useContext(RouterContext);
}

// A normal <a>, but clicks change page without a reload.
// Ctrl/Cmd-click and middle-click still open a new tab.
export function Link({ to, onClick, ...rest }) {
  function handleClick(e) {
    onClick?.(e);
    if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    e.preventDefault();
    navigate(to);
  }
  return <a href={to} onClick={handleClick} {...rest} />;
}
