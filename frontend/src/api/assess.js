// OWNER: Alier - API calls for assess
// Empty in dev: Vite proxies /api to the Flask server. Set VITE_API_URL in production.
const API = import.meta.env.VITE_API_URL || "";

async function request(path, options) {
  const res = await fetch(`${API}${path}`, options);
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(body.error || `Request failed (${res.status})`);
  return body;
}

// -> [{ id: "contact", answers: ["chat_app", "personal_email", ...] }, ...]
export function getQuestions() {
  return request("/api/assess/questions");
}

// { answers: { contact: "chat_app", ... }, context: "job" | "scholarship" | "visa" }
// -> { risk_score, verdict: "low_risk" | "suspicious" | "high_risk", flags: [questionId], context }
export function submitAssessment({ answers, context }) {
  return request("/api/assess", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ answers, context }),
  });
}
