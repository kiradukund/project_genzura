// OWNER: Abay
import { useCallback, useEffect, useState } from "react";
import { deleteAccount, getMyChecks, logout } from "../api/auth";

const PAGE_SIZE = 20;
const VERDICTS = {
  low_risk: "Low risk",
  suspicious: "Suspicious",
  high_risk: "High risk",
};

// A signed-in user's own check history, plus sign out and delete account.
// onSignedOut() is called when the session ends (sign out, delete, or expired).
export default function MyChecks({ onSignedOut = () => {} }) {
  const [checks, setChecks] = useState([]);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [confirmingDelete, setConfirmingDelete] = useState(false);
  const [busy, setBusy] = useState(false);

  const load = useCallback(
    async (offset) => {
      setLoading(true);
      setError("");
      try {
        const page = await getMyChecks({ limit: PAGE_SIZE, offset });
        setChecks((prev) =>
          offset === 0 ? page.checks : [...prev, ...page.checks],
        );
        setHasMore(page.checks.length === PAGE_SIZE);
      } catch (err) {
        if (err.status === 401) onSignedOut();
        else setError(err.message);
      } finally {
        setLoading(false);
      }
    },
    [onSignedOut],
  );

  useEffect(() => {
    load(0);
  }, [load]);

  async function handleLogout() {
    setBusy(true);
    try {
      await logout();
    } finally {
      onSignedOut();
    }
  }

  async function handleDelete() {
    setBusy(true);
    setError("");
    try {
      await deleteAccount();
      onSignedOut();
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  }

  return (
    <main className="my-checks">
      <header>
        <h1>My checks</h1>
        <button type="button" onClick={handleLogout} disabled={busy}>
          Sign out
        </button>
      </header>

      {error && (
        <p role="alert" className="my-checks-error">
          {error}
        </p>
      )}

      {!loading && !error && checks.length === 0 && (
        <p>
          You have no saved checks yet. Checks you run while signed in appear
          here.
        </p>
      )}

      <ul className="my-checks-list">
        {checks.map((c) => (
          <li key={c.id} className={`check check-${c.verdict}`}>
            <strong>{VERDICTS[c.verdict] || c.verdict}</strong>
            <span>
              {" "}
              · score {c.risk_score}/100 · {c.context}
            </span>
            <time dateTime={c.created_at}>
              {" "}
              · {new Date(c.created_at).toLocaleString()}
            </time>
            {c.masked_text && <p className="check-text">{c.masked_text}</p>}
            {c.flags?.length > 0 && (
              <p className="check-flags">
                {c.flags.map((f) => f.replace(/_/g, " ")).join(", ")}
              </p>
            )}
          </li>
        ))}
      </ul>

      {loading && <p role="status">Loading…</p>}
      {hasMore && !loading && (
        <button type="button" onClick={() => load(checks.length)}>
          Load more
        </button>
      )}

      <section className="my-checks-danger">
        <h2>Delete account</h2>
        {!confirmingDelete ? (
          <button
            type="button"
            onClick={() => setConfirmingDelete(true)}
            disabled={busy}
          >
            Delete my account
          </button>
        ) : (
          <div role="alertdialog" aria-labelledby="delete-title">
            <p id="delete-title">
              This permanently deletes your account and all your saved checks.
              It cannot be undone.
            </p>
            <button type="button" onClick={handleDelete} disabled={busy}>
              {busy ? "Deleting…" : "Yes, delete everything"}
            </button>
            <button
              type="button"
              onClick={() => setConfirmingDelete(false)}
              disabled={busy}
            >
              Cancel
            </button>
          </div>
        )}
      </section>
    </main>
  );
}
