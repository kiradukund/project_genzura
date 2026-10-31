const API_BASE = import.meta.env.VITE_API_URL || "";

export async function checkOffer(text, context) {
  const res = await fetch(`${API_BASE}/api/check`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, context }),
  });

  if (!res.ok) {
    let message = "Request failed. Please try again.";
    try {
      const body = await res.json();
      if (body.error) message = body.error;
    } catch {
      // response was not JSON, keep the default message
    }
    throw new Error(message);
  }

  return res.json();
}
