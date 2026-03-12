"use client";

import { AlertTriangle, RefreshCw } from "lucide-react";
import { useLanguage } from "@/hooks/useLanguage";

interface ErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function ErrorPage({ error, reset }: ErrorProps) {
  const { t } = useLanguage();

  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center px-4 text-center">
      <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-red-500/15">
        <AlertTriangle size={28} className="text-red-400" />
      </div>
      <h2 className="mt-4 text-lg font-semibold text-zinc-200">
        {t("error.title")}
      </h2>
      <p className="mt-1.5 max-w-sm text-sm text-zinc-500">
        {error.message || t("error.description")}
      </p>
      <button
        onClick={reset}
        className="mt-6 inline-flex items-center gap-2 rounded-xl border border-zinc-800 bg-zinc-900/60 px-5 py-2.5 text-sm font-medium text-zinc-300 transition-colors hover:border-zinc-700 hover:bg-zinc-800"
      >
        <RefreshCw size={14} />
        {t("error.retry")}
      </button>
    </div>
  );
}
