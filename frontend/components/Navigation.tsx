"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useI18n, type MessageKey } from "@/lib/i18n";

const LINKS: [string, MessageKey][] = [["/engineering", "nav.engineering"], ["/nursing", "nav.nursing"],
  ["/pharmacy", "nav.pharmacy"], ["/computing", "nav.computing"]];

export default function Navigation() {
  const current = usePathname();
  const { lang, setLang, t } = useI18n();
  return <nav className="bg-brand text-white" aria-label={t("nav.main")}>
    <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-4 py-4">
      <Link href="/" className="text-lg font-bold tracking-tight" aria-current={current === "/" ? "page" : undefined}>Credential Navigator</Link>
      <div className="flex flex-wrap items-center gap-2 text-sm font-medium">
        {LINKS.map(([href, label]) =>
          <Link key={href} href={href} aria-current={current === href ? "page" : undefined}
            className={`rounded-lg px-3 py-2 ${current === href ? "bg-white text-brand" : "hover:bg-white/15"}`}>{t(label)}</Link>)}
        <button type="button" onClick={() => setLang(lang === "en" ? "fr" : "en")} lang={lang === "en" ? "fr" : "en"}
          aria-label={t("nav.switchLanguageLabel")} className="rounded-lg border border-white/60 px-3 py-2 hover:bg-white/15">
          {t("nav.switchLanguage")}
        </button>
      </div>
    </div>
  </nav>;
}
