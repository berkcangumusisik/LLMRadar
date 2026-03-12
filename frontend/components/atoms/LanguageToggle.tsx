import { Languages } from "lucide-react";
import type { Locale } from "@/lib/i18n";

interface LanguageToggleProps {
  locale: Locale;
  onToggle: () => void;
  label: string;
  buttonText: string;
}

export function LanguageToggle({ locale, onToggle, label, buttonText }: LanguageToggleProps) {
  return (
    <button
      onClick={onToggle}
      aria-label={label}
      className="inline-flex items-center gap-1.5 rounded-lg border border-zinc-800 px-2.5 py-1.5 text-xs font-medium text-zinc-400 transition-colors hover:border-zinc-700 hover:bg-zinc-800 hover:text-zinc-200"
    >
      <Languages size={14} />
      {buttonText}
    </button>
  );
}
