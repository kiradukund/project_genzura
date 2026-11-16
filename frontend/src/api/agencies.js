// OWNER: Didier - API calls for agencies
// Empty in dev: Vite proxies /api to the Flask server. Set VITE_API_URL in production.
const API = import.meta.env.VITE_API_URL || "";

// -> { licensed_agencies: [], status, as_of, verify_with: [{ name, email?, phone? }],
//      query?, licensed? }
export async function getAgencies(name) {
  const qs = name ? `?name=${encodeURIComponent(name)}` : "";
  const res = await fetch(`${API}/api/agencies${qs}`);
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(body.error || `Request failed (${res.status})`);
  return body;
}
