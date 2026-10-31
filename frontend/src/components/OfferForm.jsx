import { useState } from "react";

const CONTEXTS = [
  { value: "job", label: "Job" },
  { value: "scholarship", label: "Scholarship" },
  { value: "visa", label: "Visa" },
];

export default function OfferForm({ onSubmit, loading }) {
  const [text, setText] = useState("");
  const [context, setContext] = useState("job");

  function handleSubmit(event) {
    event.preventDefault();
    if (!text.trim() || loading) return;
    onSubmit(text.trim(), context);
  }

  return (
    <form className="card" onSubmit={handleSubmit}>
      <label className="label" htmlFor="offer-text">
        Paste the offer message
      </label>
      <textarea
        id="offer-text"
        className="textarea"
        rows={7}
        placeholder="Paste the job, scholarship or visa message here..."
        value={text}
        onChange={(e) => setText(e.target.value)}
      />

      <div className="toggle" role="group" aria-label="Offer type">
        {CONTEXTS.map((c) => (
          <button
            key={c.value}
            type="button"
            className={context === c.value ? "toggle-btn active" : "toggle-btn"}
            aria-pressed={context === c.value}
            onClick={() => setContext(c.value)}
          >
            {c.label}
          </button>
        ))}
      </div>

      <button className="submit" type="submit" disabled={!text.trim() || loading}>
        {loading ? "Checking..." : "Check offer"}
      </button>
    </form>
  );
}
