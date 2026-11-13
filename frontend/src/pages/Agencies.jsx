// OWNER: Didier - Licensed agency search
import { useEffect, useState } from "react";
import { useI18n } from "../i18n";
import { getAgencies } from "../api/agencies.js";

export default function Agencies() {
  const { t } = useI18n();
  const [info, setInfo] = useState(null);
  const [status, setStatus] = useState("loading");
  const [name, setName] = useState("");
  const [result, setResult] = useState(null);

  useEffect(() => {
    getAgencies()
      .then((data) => {
        setInfo(data);
        setStatus("ready");
      })
      .catch(() => setStatus("error"));
  }, []);

  function onSearch(e) {
    e.preventDefault();
    if (!name.trim()) return;
    getAgencies(name.trim())
      .then(setResult)
      .catch(() => setStatus("error"));
  }

  return (
    <section className="section">
      <h1>{t("agencies.title")}</h1>
      <p className="section-intro">{t("agencies.warning")}</p>

      <form onSubmit={onSearch}>
        <label htmlFor="agency-name">{t("agencies.searchLabel")}</label>
        <input
          id="agency-name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder={t("agencies.placeholder")}
        />
        <button type="submit">{t("agencies.check")}</button>
      </form>

      {result && (
        <p role="status">
          {result.licensed
            ? t("agencies.licensed")
            : `${result.query}: ${t("agencies.notLicensed")}`}
        </p>
      )}

      {status === "loading" && <p>{t("agencies.loading")}</p>}
      {status === "error" && <p>{t("agencies.error")}</p>}

      {status === "ready" && (
        <>
          <h2>{t("agencies.verifyTitle")}</h2>
          <ul>
            {info.verify_with.map((c) => (
              <li key={c.name}>
                {c.name}
                {c.phone && <> · <a href={`tel:${c.phone}`}>{c.phone}</a></>}
                {c.email && <> · <a href={`mailto:${c.email}`}>{c.email}</a></>}
              </li>
            ))}
          </ul>
          <p><small>{t("agencies.asOf")} {info.as_of}</small></p>
        </>
      )}
    </section>
  );
}
