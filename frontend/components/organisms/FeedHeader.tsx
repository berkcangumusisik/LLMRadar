"use client";

import { Radar } from "lucide-react";
import { LanguageToggle, LiveBadge } from "@/components/atoms";
import { useLanguage } from "@/hooks/useLanguage";

interface FeedHeaderProps {
  isConnected: boolean;
  totalArticles: number;
}

export function FeedHeader({ isConnected, totalArticles }: FeedHeaderProps) {
  const { locale, toggle, t } = useLanguage();

  return (
    <header className="flex items-center justify-between">
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-violet-600/20">
          <Radar size={22} className="text-violet-400" />
        </div>
        <div>
          <h1 className="text-xl font-bold tracking-tight text-zinc-100">
            LLMRadar
          </h1>
          <p className="text-xs text-zinc-500">
            {totalArticles > 0
              ? t("header.subtitle.tracking", { count: totalArticles })
              : t("header.subtitle.default")}
          </p>
        </div>
      </div>
      <div className="flex items-center gap-3">
        <LanguageToggle
          locale={locale}
          onToggle={toggle}
          label={t("lang.label")}
          buttonText={t("lang.switch")}
        />
        <LiveBadge
          isConnected={isConnected}
          connectedText={t("live.connected")}
          disconnectedText={t("live.disconnected")}
        />
      </div>
    </header>
  );
}
