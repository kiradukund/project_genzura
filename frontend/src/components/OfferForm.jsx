import { useI18n } from "../i18n";
import ScreenshotUpload from "./ScreenshotUpload";

export const MAX_CHARS = 2000;

export default function OfferForm({ text, onTextChange, onSubmit, loading, error }) {
  const { t } = useI18n();

  function appendOcrText(extracted) {
    // Append so the user can review and edit before checking.
    const next = (text ? `${text}\n` : "") + extracted;
    onTextChange(next.slice(0, MAX_CHARS));
  }

  function handleSubmit(e) {
    e.preventDefault();
    if (text.trim() && !loading) onSubmit();
  }

  return (
    <form className="offer-form" onSubmit={handleSubmit}>
      <label htmlFor="offer-text" className="sr-only">
        {t("form.label")}
      </label>
      <textarea
        id="offer-text"
        maxLength={MAX_CHARS}
        placeholder={t("form.placeholder")}
        value={text}
        onChange={(e) => onTextChange(e.target.value)}
      />
      <div className="counter" aria-live="polite">
        {text.length}/{MAX_CHARS}
      </div>

      <ScreenshotUpload onText={appendOcrText} disabled={loading} />

      <button type="submit" className="btn-primary" disabled={!text.trim() || loading}>
        {loading ? t("form.checking") : t("form.check")}
      </button>
      {error && <p className="error" role="alert">{error}</p>}
    </form>
  );
}
