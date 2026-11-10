import "./Directory.css";
import { useState } from "react";
import { useI18n } from "../i18n";
import { directoryEntries } from "../data/directoryEntries.js";

export default function Directory() {
  const { t } = useI18n();
  const [query, setQuery] = useState("");
  const q = query.trim().toLowerCase();

  const matches = directoryEntries.filter(
    (e) => e.name.toLowerCase().includes(q) || e.category.toLowerCase().includes(q)
  );

  return (
    <div className="directory">
      <h2 className="section-title">{t("directory.title")}</h2>
      <p className="section-intro">{t("directory.intro")}</p>
      <input
        type="search"
        placeholder={t("directory.search")}
        aria-label={t("directory.search")}
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />
      {matches.length === 0 && <p>{t("directory.empty")}</p>}
      <ul className="directory-list">
        {matches.map((e) => (
          <li key={e.name} className="directory-card">
            <h3>{e.name}</h3>
            <p>{e.category}</p>
            <p>
              <a href={`tel:${e.phone.replace(/[\s()]/g, "")}`}>{e.phone}</a>
            </p>
            <p>{e.website}</p>
            <p className="verified">
              {t("directory.verified")} · {t("directory.lastVerified")}: {e.lastVerified}
            </p>
          </li>
        ))}
      </ul>
    </div>
  );
}
