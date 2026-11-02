import { createContext, useContext, useEffect, useState } from "react";
import en from "./en.json";
import rw from "./rw.json";

// Alier adds the Kinyarwanda wording to rw.json. Any key missing from rw.json
// falls back to English, so untranslated text never shows up blank.
const DICTS = { en, rw };
export const LANGUAGES = ["en", "rw"];
const STORAGE_KEY = "genzura.lang";

function lookup(dict, key) {
  return key.split(".").reduce((node, part) => (node == null ? undefined : node[part]), dict);
}

function initialLanguage() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (LANGUAGES.includes(saved)) return saved;
  } catch {
    // storage blocked: use the default
  }
  return "en";
}

const I18nContext = createContext(null);

export function I18nProvider({ children }) {
  const [lang, setLang] = useState(initialLanguage);

  useEffect(() => {
    document.documentElement.lang = lang;
    try {
      localStorage.setItem(STORAGE_KEY, lang);
    } catch {
      // ignore
    }
  }, [lang]);

  const t = (key) => {
    const value = lookup(DICTS[lang], key) ?? lookup(en, key);
    return typeof value === "string" ? value : key;
  };
  const has = (key) => typeof lookup(en, key) === "string";

  return <I18nContext.Provider value={{ lang, setLang, t, has }}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  return useContext(I18nContext);
}
