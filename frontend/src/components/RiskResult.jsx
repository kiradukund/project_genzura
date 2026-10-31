const VERDICTS = {
  low_risk: { label: "Low risk", className: "low" },
  suspicious: { label: "Suspicious", className: "medium" },
  high_risk: { label: "High risk", className: "high" },
};

const RIB_PHONE = "166";
const RIB_WEBSITE = "https://www.rib.gov.rw";

function formatFlag(flag) {
  const text = flag.replace(/_/g, " ");
  return text.charAt(0).toUpperCase() + text.slice(1);
}

export default function RiskResult({ result }) {
  const verdict = VERDICTS[result.verdict] || VERDICTS.low_risk;
  const flags = result.flags || [];
  const showRib = result.verdict === "suspicious" || result.verdict === "high_risk";

  return (
    <section className={`card result ${verdict.className}`} aria-live="polite">
      <div className="result-head">
        <span className="badge">{verdict.label}</span>
        <span className="score">Risk score: {result.risk_score} / 100</span>
      </div>

      {flags.length > 0 ? (
        <>
          <h2 className="result-title">Warning signs found</h2>
          <ul className="flags">
            {flags.map((flag) => (
              <li key={flag}>{formatFlag(flag)}</li>
            ))}
          </ul>
        </>
      ) : (
        <p className="muted">No warning signs were detected in this message.</p>
      )}

      {showRib && (
        <div className="rib">
          <p className="rib-text">
            Think this is a scam? Report it to the Rwanda Investigation Bureau (RIB).
          </p>
          <div className="rib-actions">
            <a className="rib-btn" href={`tel:${RIB_PHONE}`}>
              Call RIB: {RIB_PHONE}
            </a>
            <a
              className="rib-btn secondary"
              href={RIB_WEBSITE}
              target="_blank"
              rel="noopener noreferrer"
            >
              RIB website
            </a>
          </div>
        </div>
      )}
    </section>
  );
}
