import { useRef, useState } from "react";
import { useI18n } from "../i18n";

const MAX_BYTES = 5 * 1024 * 1024;

// OCR runs in the browser with Tesseract.js, so the image never leaves the phone.
// Only the extracted text goes into the form (and later to POST /api/check).
export default function ScreenshotUpload({ onText, disabled }) {
  const { t } = useI18n();
  const inputRef = useRef(null);
  const [busy, setBusy] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState("");

  async function handleFile(e) {
    const file = e.target.files?.[0];
    e.target.value = ""; // allow picking the same file again
    if (!file) return;

    setError("");
    if (!file.type.startsWith("image/")) return setError(t("upload.notImage"));
    if (file.size > MAX_BYTES) return setError(t("upload.tooBig"));

    setBusy(true);
    setProgress(0);
    try {
      // Loaded on demand so the first page load stays small on slow connections.
      const { default: Tesseract } = await import("tesseract.js");
      const { data } = await Tesseract.recognize(file, "eng", {
        logger: (m) => {
          if (m.status === "recognizing text") setProgress(Math.round(m.progress * 100));
        },
      });
      const text = data.text.trim();
      if (text) onText(text);
      else setError(t("upload.noText"));
    } catch {
      setError(t("upload.failed"));
    } finally {
      setBusy(false);
      setProgress(0);
    }
  }

  return (
    <div className="upload">
      <button
        type="button"
        className="btn-outline"
        disabled={busy || disabled}
        onClick={() => inputRef.current?.click()}
      >
        <svg viewBox="0 0 24 24" aria-hidden="true" className="icon">
          <path
            d="M4 7h3l2-3h6l2 3h3v13H4z M12 17a4 4 0 1 0 0-8 4 4 0 0 0 0 8z"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinejoin="round"
          />
        </svg>
        {busy ? `${t("upload.reading")} ${progress}%` : t("upload.button")}
      </button>
      {busy && (
        <div className="progress" role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={progress}>
          <div style={{ width: `${progress}%` }} />
        </div>
      )}
      <p className="hint">{t("upload.hint")}</p>
      {error && <p className="error" role="alert">{error}</p>}
      <input ref={inputRef} type="file" accept="image/*" hidden onChange={handleFile} />
    </div>
  );
}
