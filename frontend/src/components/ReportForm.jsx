// OWNER: Chol - Report a scam form
import { useState } from "react";
import { submitReport } from "../api/reports";

export default function ReportForm({ checkId }) {
  const [text, setText] = useState("");
  const [contact, setContact] = useState("");
  const [status, setStatus] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    setStatus("sending");
    try {
      await submitReport({ text, contact, check_id: checkId });
      setStatus("done");
    } catch {
      setStatus("error");
    }
  }

  if (status === "done") return <p>Thank you. Your report has been submitted.</p>;

  return (
    <form onSubmit={handleSubmit}>
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Paste the suspicious message here"
        required
        rows={4}
      />
      <input
        value={contact}
        onChange={(e) => setContact(e.target.value)}
        placeholder="Your phone or email (optional)"
      />
      <button type="submit" disabled={status === "sending"}>
        {status === "sending" ? "Submitting..." : "Report this scam"}
      </button>
      {status === "error" && <p>Something went wrong. Please try again.</p>}
    </form>
  );
}
