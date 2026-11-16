// OWNER: Kuol - API calls for alerts
import { post } from "./client";

// { phone: "07X XXX XXXX", language: "en" | "rw" } -> { subscribed: true }
export function subscribeAlerts({ phone, language }) {
  return post("/api/alerts/subscribe", { phone, language });
}

// { phone } -> { unsubscribed: true }
export function unsubscribeAlerts({ phone }) {
  return post("/api/alerts/unsubscribe", { phone });
}
