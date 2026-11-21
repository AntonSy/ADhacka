import type { Metadata } from "next";
import "./globals.css";
import { SiteNav } from "@/components/site-nav";

export const metadata: Metadata = {
  title: "Analyst Days: проверка аннотации доклада",
  description: "Сверка аннотации с ранее принятыми докладами конференции Analyst Days",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru">
      <body>
        <header className="bg-slate-900 px-6 py-4 text-white">
          <h1 className="text-xl font-semibold">Analyst Days: проверка аннотации доклада</h1>
          <p className="text-sm text-slate-300">Сверка аннотации с ранее принятыми докладами конференции</p>
        </header>
        <SiteNav />
        <main className="mx-auto max-w-4xl space-y-4 p-4">{children}</main>
      </body>
    </html>
  );
}
