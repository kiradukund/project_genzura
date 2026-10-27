import { useEffect, useState } from "react";

export default function App() {
  const [status, setStatus] = useState("Checking API...");

  useEffect(() => {
    fetch("/health")
      .then((res) => res.json())
      .then((data) => setStatus(data.status))
      .catch(() => setStatus("API not reachable"));
  }, []);

  return (
    <div style={{ fontFamily: "sans-serif", padding: "2rem" }}>
      <h1>Genzura</h1>
      <p>{status}</p>
    </div>
  );
}