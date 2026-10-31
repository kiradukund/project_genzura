import { useState } from "react";
import Header from "./components/Header.jsx";
import OfferForm from "./components/OfferForm.jsx";
import RiskResult from "./components/RiskResult.jsx";
import { checkOffer } from "./api/client.js";
import "./styles.css";

export default function App() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(text, context) {
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const data = await checkOffer(text, context);
      setResult(data);
    } catch (err) {
      setError(err.message || "Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app">
      <Header />
      <main className="main">
        <OfferForm onSubmit={handleSubmit} loading={loading} />
        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}
        {result && <RiskResult result={result} />}
      </main>
    </div>
  );
}
