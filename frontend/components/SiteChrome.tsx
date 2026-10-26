"use client";

import Link from "next/link";
import Navigation from "./Navigation";
import { LanguageProvider, useI18n } from "@/lib/i18n";

function Chrome({ children }: { children: React.ReactNode }) {
  const { t } = useI18n();
  return (
    <>
      <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:p-2 focus:bg-white">{t("site.skip")}</a>
      <header>
        <Navigation />
        <div role="note" className="border-b border-amber-300 bg-amber-50">
          <p className="mx-auto max-w-6xl px-4 py-2 text-sm text-amber-900">
            <strong>{t("site.advisoryLead")}</strong> {t("site.advisory")}
          </p>
        </div>
      </header>
      <main id="main" className="mx-auto max-w-6xl px-4 py-8">{children}</main>
      <footer className="mx-auto max-w-6xl px-4 pb-10 text-xs text-slate-600">
        {t("site.footer")} <Link href="/privacy" className="underline">{t("site.privacy")}</Link>
      </footer>
    </>
  );
}

export default function SiteChrome({ children }: { children: React.ReactNode }) {
  return <LanguageProvider><Chrome>{children}</Chrome></LanguageProvider>;
}
