// OWNER: Chol - API calls for reports
const BASE = import.meta.env.VITE_API_URL ?? "";

export async function submitReport({ text, contact, check_id }) {
  const res = await fetch(`${BASE}/api/reports`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, contact, check_id }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function fetchReports(status = "pending") {
  const res = await fetch(`${BASE}/api/admin/reports?status=${status}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function approveReport(id, admin_email, note = "") {
  const res = await fetch(`${BASE}/api/admin/reports/${id}/approve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ admin_email, note }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function rejectReport(id, admin_email, note = "") {
  const res = await fetch(`${BASE}/api/admin/reports/${id}/reject`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ admin_email, note }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
