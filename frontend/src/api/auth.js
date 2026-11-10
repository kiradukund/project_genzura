// OWNER: Abay
// Client for the Flask auth endpoints.
// The session is an httpOnly cookie: this code never sees or stores a token,
// it only has to send `credentials: "include"` with every request.

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:5000";

export class ApiError extends Error {
  constructor(message, status, data = null) {
    super(message);
    this.name = "ApiError";
    this.status = status; // 0 means the server could not be reached
    this.data = data; // the JSON body, e.g. { error, attempts_left }
  }
}

async function request(path, { method = "GET", body } = {}) {
  let res;
  try {
    res = await fetch(`${API_URL}${path}`, {
      method,
      credentials: "include",
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError("Cannot reach the server. Check your connection.", 0);
  }

  let data = null;
  try {
    data = await res.json();
  } catch {
    // some responses have no body
  }
  if (!res.ok) {
    throw new ApiError(
      data?.error || "Something went wrong.",
      res.status,
      data,
    );
  }
  return data;
}

// ---- phone + SMS code ----
export const requestCode = (phone) =>
  request("/api/auth/phone/request", { method: "POST", body: { phone } });

export const verifyCode = (phone, code) =>
  request("/api/auth/phone/verify", { method: "POST", body: { phone, code } });

// ---- admin ----
export const adminLogin = (email, password) =>
  request("/api/auth/admin/login", {
    method: "POST",
    body: { email, password },
  });

// ---- session and account ----

// Resolves to { kind: "user" | "admin", ... }, or null when nobody is signed in.
export async function getSession() {
  try {
    return await request("/api/auth/me");
  } catch (err) {
    if (err.status === 401) return null;
    throw err;
  }
}

export const logout = () => request("/api/auth/logout", { method: "POST" });

export const deleteAccount = () =>
  request("/api/auth/account", { method: "DELETE" });

// Resolves to { checks, limit, offset }
export const getMyChecks = ({ limit = 20, offset = 0 } = {}) =>
  request(`/api/me/checks?limit=${limit}&offset=${offset}`);
