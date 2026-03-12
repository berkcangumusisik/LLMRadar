import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { LanguageProvider } from "@/hooks/useLanguage";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "LLMRadar — Real-time LLM News Aggregator",
  description:
    "Track the latest news about GPT, Claude, Gemini, Llama, DeepSeek and more. Real-time AI news feed with smart summaries and related articles.",
  keywords: [
    "LLM",
    "AI news",
    "GPT",
    "Claude",
    "Gemini",
    "Llama",
    "DeepSeek",
    "machine learning",
  ],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="tr" className="dark">
      <body
        className={`${inter.className} min-h-screen bg-zinc-950 text-zinc-100 antialiased`}
      >
        <LanguageProvider>
          {children}
        </LanguageProvider>
      </body>
    </html>
  );
}
