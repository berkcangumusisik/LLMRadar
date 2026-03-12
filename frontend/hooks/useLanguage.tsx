"use client";

import {
  createContext,
  useCallback,
  useContext,
  useState,
  type ReactNode,
} from "react";
import { t, type Locale, type TranslationKey } from "@/lib/i18n";

interface LanguageContextValue {
  locale: Locale;
  toggle: () => void;
  t: (key: TranslationKey, vars?: Record<string, string | number>) => string;
}

const LanguageContext = createContext<LanguageContextValue | null>(null);

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [locale, setLocale] = useState<Locale>("tr");

  const toggle = useCallback(() => {
    setLocale((prev) => (prev === "tr" ? "en" : "tr"));
  }, []);

  const translate = useCallback(
    (key: TranslationKey, vars?: Record<string, string | number>) =>
      t(key, locale, vars),
    [locale],
  );

  return (
    <LanguageContext.Provider value={{ locale, toggle, t: translate }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage(): LanguageContextValue {
  const ctx = useContext(LanguageContext);
  if (!ctx) throw new Error("useLanguage must be used within LanguageProvider");
  return ctx;
}
