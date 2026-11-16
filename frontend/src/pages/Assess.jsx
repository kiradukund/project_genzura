// OWNER: Alier - Guided assessment page
import "./Assess.css";
import { useEffect, useState } from "react";
import { getQuestions, submitAssessment } from "../api/assess";
import ActionButtons from "../components/ActionButtons";
import OfferTypeToggle from "../components/OfferTypeToggle";
import { useI18n } from "../i18n";

// One question at a time, then the result. The question order and the answer
// ids come from the API (backend/app/assess.py); the words come from en.json / rw.json.
export default function Assess() {
  const { t } = useI18n();
  const [questions, setQuestions] = useState([]);
  const [context, setContext] = useState("job");
  const [step, setStep] = useState(0);
  const [answers, setAnswers] = useState({});
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    getQuestions()
      .then(setQuestions)
      .catch(() => setError(t("assess.error")));
    // Load once; t() changes with the language but the questions do not.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const question = questions[step];
  const isLast = step === questions.length - 1;
  const chosen = question ? answers[question.id] : undefined;

  function choose(answerId) {
    setAnswers((prev) => ({ ...prev, [question.id]: answerId }));
  }

  async function submit() {
    setLoading(true);
    setError("");
    try {
      setResult(await submitAssessment({ answers, context }));
    } catch {
      setError(t("assess.error"));
    } finally {
      setLoading(false);
    }
  }

  function restart() {
    setAnswers({});
    setStep(0);
    setResult(null);
    setError("");
  }

  if (result) {
    const verdict = result.verdict || "low_risk";
    return (
      <div className="assess">
        <section className={`result result-${verdict}`} aria-live="polite">
          <div className="badge">{t(`risk.${verdict}`)}</div>
          <p className="explain">{t(`explain.${verdict}`)}</p>
          <div className="score">
            <span>{t("score")}</span>
            <div className="meter" aria-hidden="true">
              <div style={{ width: `${Math.min(100, result.risk_score)}%` }} />
            </div>
            <strong>{result.risk_score}/100</strong>
          </div>

          <h2>{t("assess.reasonsTitle")}</h2>
          {result.flags.length === 0 ? (
            <p className="muted">{t("assess.noReasons")}</p>
          ) : (
            <ul className="flags">
              {result.flags.map((id) => (
                <li key={id}>{t(`assess.reasons.${id}`)}</li>
              ))}
            </ul>
          )}

          <h2>{t("nextSteps")}</h2>
          <ActionButtons />
          <button type="button" className="btn-outline assess-restart" onClick={restart}>
            {t("assess.startAgain")}
          </button>
        </section>
      </div>
    );
  }

  return (
    <div className="assess">
      <h2 className="section-title">{t("assess.title")}</h2>
      <p className="section-intro">{t("assess.intro")}</p>

      {step === 0 && <OfferTypeToggle value={context} onChange={setContext} />}

      {question && (
        <fieldset className="assess-question">
          <legend>
            <span className="assess-progress">
              {t("assess.question")} {step + 1} / {questions.length}
            </span>
            {t(`assess.questions.${question.id}.q`)}
          </legend>

          <div className="assess-answers">
            {question.answers.map((answerId) => (
              <label key={answerId} className={chosen === answerId ? "assess-answer active" : "assess-answer"}>
                <input
                  type="radio"
                  name={question.id}
                  value={answerId}
                  checked={chosen === answerId}
                  onChange={() => choose(answerId)}
                />
                {t(`assess.questions.${question.id}.${answerId}`)}
              </label>
            ))}
          </div>
        </fieldset>
      )}

      {error && (
        <p className="assess-error" role="alert">
          {error}
        </p>
      )}

      {question && (
        <div className="assess-nav">
          {step > 0 && (
            <button type="button" className="btn-outline" onClick={() => setStep(step - 1)}>
              {t("assess.back")}
            </button>
          )}
          {isLast ? (
            <button type="button" className="btn-primary" disabled={!chosen || loading} onClick={submit}>
              {loading ? t("assess.checking") : t("assess.seeResult")}
            </button>
          ) : (
            <button type="button" className="btn-primary" disabled={!chosen} onClick={() => setStep(step + 1)}>
              {t("assess.next")}
            </button>
          )}
        </div>
      )}
    </div>
  );
}
