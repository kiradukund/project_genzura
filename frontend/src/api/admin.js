// OWNER: Didier - API calls for admin
// Empty in dev: Vite proxies /api to the Flask server. Set VITE_API_URL in production.
const API = import.meta.env.VITE_API_URL || "";

async function request(path, options) {
  const res = await fetch(`${API}${path}`, { credentials: "include", ...options });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(body.error || `Request failed (${res.status})`);
  return body;
}

// -> { total, by_verdict: { low_risk, suspicious, high_risk }, by_context: { job, scholarship, visa },
//      top_flags: [{ flag, count }], per_day: [{ day, count }] }
export function getStats() {
  return request("/api/admin/stats");
}