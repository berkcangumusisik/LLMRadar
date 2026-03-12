"use client";

import { useState } from "react";

interface SummaryToggleProps {
  summaryTr: string | null;
  summaryEn: string | null;
}

export function SummaryToggle({ summaryTr, summaryEn }: SummaryToggleProps) {
  const [lang, setLang] = useState<"tr" | "en">("tr");

  const text = lang === "tr" ? summaryTr : summaryEn;
  if (!text) return null;

  return (
    <div className="space-y-1.5">
      <div className="flex gap-1">
        <button
          onClick={() => setLang("tr")}
          className={`rounded px-2 py-0.5 text-xs font-medium transition-colors ${
            lang === "tr"
              ? "bg-zinc-700 text-zinc-100"
              : "text-zinc-500 hover:text-zinc-300"
          }`}
        >
          TR
        </button>
        <button
          onClick={() => setLang("en")}
          className={`rounded px-2 py-0.5 text-xs font-medium transition-colors ${
            lang === "en"
              ? "bg-zinc-700 text-zinc-100"
              : "text-zinc-500 hover:text-zinc-300"
          }`}
        >
          EN
        </button>
      </div>
      <p className="text-sm leading-relaxed text-zinc-300">{text}</p>
    </div>
  );
}
