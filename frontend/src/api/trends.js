// OWNER: Alier - API calls for trends
// Empty in dev: Vite proxies /api to the Flask server. Set VITE_API_URL in production.
const API = import.meta.env.VITE_API_URL || "";

// days: 7 or 30
// -> { days, total, enough_data, flags: [{ id, count }], contexts: [{ id, count }] }
export async function getTrends(days) {
  const res = await fetch(`${API}/api/trends?days=${days}`);
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(body.error || `Request failed (${res.status})`);
  return body;
}
