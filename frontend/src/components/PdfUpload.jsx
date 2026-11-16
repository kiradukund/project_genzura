// OWNER: Kevin - Read offer letters (PDF) in the browser
import { useRef, useState } from "react";
import { useI18n } from "../i18n";

const MAX_BYTES = 10 * 1024 * 1024;
const MAX_PAGES = 5;      // offer letters are short; this keeps old phones fast
const MAX_OCR_PAGES = 2;  // scanned letters: read the first pages as images
const MIN_TEXT = 30;      // less than this means the PDF is a scan, not text

// Loaded only when someone picks a PDF, so the home page stays small.
async function loadPdfJs() {
  const pdfjs = await import("pdfjs-dist");
  const { default: workerUrl } = await import("pdfjs-dist/build/pdf.worker.min.mjs?url");
  pdfjs.GlobalWorkerOptions.workerSrc = workerUrl;
  return pdfjs;
}

async function pageText(page) {
  const content = await page.getTextContent();
  return content.items.map((item) => item.str + (item.hasEOL ? "\n" : " ")).join("");
}

async function pageImageText(page, Tesseract) {
  const viewport = page.getViewport({ scale: 2 });
  const canvas = document.createElement("canvas");
  canvas.width = viewport.width;
  canvas.height = viewport.height;
  await page.render({ canvasContext: canvas.getContext("2d"), viewport }).promise;
  const { data } = await Tesseract.recognize(canvas, "eng");
  return data.text;
}

// Like ScreenshotUpload: the PDF never leaves the phone. Only the text goes into the form.
export default function PdfUpload({ onText, disabled }) {
  const { t } = useI18n();
  const inputRef = useRef(null);
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");

  async function handleFile(e) {
    const file = e.target.files?.[0];
    e.target.value = ""; // allow picking the same file again
    if (!file) return;

    setError("");
    const isPdf = file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf");
    if (!isPdf) return setError(t("pdfUpload.notPdf"));
    if (file.size > MAX_BYTES) return setError(t("pdfUpload.tooBig"));

    setStatus(t("pdfUpload.reading"));
    let pdf;
    try {
      const pdfjs = await loadPdfJs();
      pdf = await pdfjs.getDocument({ data: await file.arrayBuffer(), isEvalSupported: false }).promise;
      const pages = Math.min(pdf.numPages, MAX_PAGES);

      let text = "";
      for (let n = 1; n <= pages; n += 1) text += (await pageText(await pdf.getPage(n))) + "\n";

      if (text.replace(/\s/g, "").length < MIN_TEXT) {
        // A scanned letter: no text inside, so read the page images instead.
        setStatus(t("pdfUpload.scanned"));
        const { default: Tesseract } = await import("tesseract.js");
        text = "";
        for (let n = 1; n <= Math.min(pages, MAX_OCR_PAGES); n += 1) {
          text += (await pageImageText(await pdf.getPage(n), Tesseract)) + "\n";
        }
      }

      text = text.replace(/[ \t]+/g, " ").replace(/\n{3,}/g, "\n\n").trim();
      if (text) onText(text);
      else setError(t("pdfUpload.noText"));
    } catch (err) {
      setError(err?.name === "PasswordException" ? t("pdfUpload.locked") : t("pdfUpload.failed"));
    } finally {
      pdf?.destroy();
      setStatus("");
    }
  }

  return (
    <div className="upload">
      <button
        type="button"
        className="btn-outline"
        disabled={Boolean(status) || disabled}
        onClick={() => inputRef.current?.click()}
      >
        <svg viewBox="0 0 24 24" aria-hidden="true" className="icon">
          <path
            d="M6 2h9l5 5v15H6z M14 2v6h6 M9 13h8 M9 17h8"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinejoin="round"
          />
        </svg>
        {status || t("pdfUpload.button")}
      </button>
      <p className="hint">{t("pdfUpload.hint")}</p>
      {error && <p className="error" role="alert">{error}</p>}
      <input ref={inputRef} type="file" accept="application/pdf,.pdf" hidden onChange={handleFile} />
    </div>
  );
}
