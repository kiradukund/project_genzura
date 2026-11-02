import { useI18n } from "../i18n";

const ITEMS = ["1", "2", "3", "4", "5", "6"];

// Native <details> elements: accessible and work without extra JavaScript.
export default function Faq() {
  const { t } = useI18n();

  return (
    <div className="faq">
      {ITEMS.map((n) => (
        <details key={n}>
          <summary>{t(`faq.items.${n}.q`)}</summary>
          <p>{t(`faq.items.${n}.a`)}</p>
        </details>
      ))}
    </div>
  );
}
