"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { en, type MessageKey } from "./messages/en";
import { fr } from "./messages/fr";

export type Lang = "en" | "fr";
const STORAGE_KEY = "navigator-lang";
const MESSAGES: Record<Lang, Record<MessageKey, string>> = { en, fr };

const LanguageContext = createContext<{ lang: Lang; setLang: (lang: Lang) => void }>({ lang: "en", setLang: () => {} });

/** English by default; a saved choice or a French browser switches to French after the first render. */
export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [lang, setLangState] = useState<Lang>("en");
  useEffect(() => {
    let saved: string | null = null;
    try { saved = localStorage.getItem(STORAGE_KEY); } catch { /* storage unavailable: use the browser language */ }
    if (saved === "en" || saved === "fr") setLangState(saved);
    else if (navigator.language.toLowerCase().startsWith("fr")) setLangState("fr");
  }, []);
  useEffect(() => { document.documentElement.lang = lang === "fr" ? "fr-CA" : "en-CA"; }, [lang]);
  const setLang = useCallback((next: Lang) => {
    setLangState(next);
    try { localStorage.setItem(STORAGE_KEY, next); } catch { /* the choice lasts until the page is closed */ }
  }, []);
  return <LanguageContext.Provider value={{ lang, setLang }}>{children}</LanguageContext.Provider>;
}

export function useI18n() {
  const { lang, setLang } = useContext(LanguageContext);
  const t = useCallback((key: MessageKey, vars?: Record<string, string | number>) => {
    let text = MESSAGES[lang][key];
    for (const [name, value] of Object.entries(vars ?? {})) text = text.replaceAll(`{${name}}`, String(value));
    return text;
  }, [lang]);
  return { lang, setLang, t };
}

export type { MessageKey };
