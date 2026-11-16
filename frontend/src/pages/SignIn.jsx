// OWNER: Abay
import { useState } from "react";
import { adminLogin, getSession, requestCode, verifyCode } from "../api/auth";

// Sign in with a phone number + SMS code, or (for the team) email + password.
// onSignedIn(session) is called with { kind: "user" | "admin", ... } once the
// cookie is set, so the parent decides where to go next.
export default function SignIn({ onSignedIn = () => {} }) {
  const [mode, setMode] = useState("phone"); // "phone" | "admin"
  const [step, setStep] = useState("phone"); // phone mode: "phone" -> "code"
  const [phone, setPhone] = useState("");
  const [code, setCode] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  async function run(action) {
    setError("");
    setNotice("");
    setBusy(true);
    try {
      await action();
    } catch (err) {
      setError(describe(err));
    } finally {
      setBusy(false);
    }
  }

  async function finish() {
    onSignedIn(await getSession());
  }

  function sendCode(event) {
    event?.preventDefault();
    return run(async () => {
      await requestCode(phone.trim());
      setCode("");
      setStep("code");
      setNotice("We sent a 6-digit code by SMS. It expires in 5 minutes.");
    });
  }

  function submitCode(event) {
    event.preventDefault();
    return run(async () => {
      await verifyCode(phone.trim(), code);
      await finish();
    });
  }

  function submitAdmin(event) {
    event.preventDefault();
    return run(async () => {
      await adminLogin(email.trim(), password);
      await finish();
    });
  }

  function switchMode(next) {
    setMode(next);
    setStep("phone");
    setError("");
    setNotice("");
  }

  return (
    <main className="signin">
      <h1>Sign in to Genzura</h1>

      <div role="tablist" className="signin-tabs">
        <button
          type="button"
          role="tab"
          aria-selected={mode === "phone"}
          onClick={() => switchMode("phone")}
        >
          Phone
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={mode === "admin"}
          onClick={() => switchMode("admin")}
        >
          Team login
        </button>
      </div>

      {error && (
        <p role="alert" className="signin-error">
          {error}
        </p>
      )}
      {notice && (
        <p role="status" className="signin-notice">
          {notice}
        </p>
      )}

      {mode === "phone" && step === "phone" && (
        <form onSubmit={sendCode}>
          <label htmlFor="phone">Phone number</label>
          <input
            id="phone"
            type="tel"
            autoComplete="tel"
            placeholder="0788 123 456"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            required
          />
          <button type="submit" disabled={busy || !phone.trim()}>
            {busy ? "Sending…" : "Send code"}
          </button>
          <p className="signin-hint">
            We never store your number, only a scrambled version of it.
          </p>
        </form>
      )}

      {mode === "phone" && step === "code" && (
        <form onSubmit={submitCode}>
          <label htmlFor="code">6-digit code sent to {phone}</label>
          <input
            id="code"
            inputMode="numeric"
            autoComplete="one-time-code"
            maxLength={6}
            pattern="\d{6}"
            value={code}
            onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
            required
          />
          <button type="submit" disabled={busy || code.length !== 6}>
            {busy ? "Checking…" : "Sign in"}
          </button>
          <div className="signin-links">
            <button type="button" disabled={busy} onClick={sendCode}>
              Send a new code
            </button>
            <button
              type="button"
              disabled={busy}
              onClick={() => setStep("phone")}
            >
              Use a different number
            </button>
          </div>
        </form>
      )}

      {mode === "admin" && (
        <form onSubmit={submitAdmin}>
          <label htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            autoComplete="username"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <label htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          <button type="submit" disabled={busy || !email.trim() || !password}>
            {busy ? "Signing in…" : "Sign in"}
          </button>
        </form>
      )}
    </main>
  );
}

function describe(err) {
  const left = err.data?.attempts_left;
  if (typeof left === "number") {
    return left > 0
      ? `${err.message}. ${left} ${left === 1 ? "attempt" : "attempts"} left.`
      : `${err.message}. Request a new code.`;
  }
  return err.message || "Something went wrong.";
}
