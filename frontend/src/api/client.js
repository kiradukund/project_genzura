// Empty in dev: Vite proxies /api to the Flask server. Set VITE_API_URL in production.
const API = import.meta.env.VITE_API_URL || "";

async function post(path, payload) {
  const res = await fetch(`${API}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(body.error || `Request failed (${res.status})`);
  return body;
}

// { text, context: "job" | "scholarship" | "visa", language: "en" | "rw" }
// -> { risk_score, verdict: "low_risk" | "suspicious" | "high_risk", flags: [ruleId], check_id }
export function checkOffer(payload) {
  return post("/api/check", payload);
}

// "Send result to my phone". The backend endpoint is not built yet;
// the form only shows when VITE_ENABLE_SMS_RESULT=true.
export function sendResultSms({ phone, checkId, language }) {
  return post("/api/send-result", { phone, check_id: checkId, language });
}
