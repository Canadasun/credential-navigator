"use client";

import Link from "next/link";
import { useI18n, type MessageKey } from "@/lib/i18n";

const professions: { href: string; key: "engineering" | "nursing" | "pharmacy" | "computing" }[] = [
  { href: "/engineering", key: "engineering" },
  { href: "/nursing", key: "nursing" },
  { href: "/pharmacy", key: "pharmacy" },
  { href: "/computing", key: "computing" },
];
const steps: [string, MessageKey, MessageKey][] = [["01", "home.step1", "home.step1Text"],
  ["02", "home.step2", "home.step2Text"], ["03", "home.step3", "home.step3Text"]];

export default function Home() {
  const { t } = useI18n();
  return (
    <div className="space-y-8">
      <section className="rounded-2xl border border-slate-200 bg-white px-6 py-8 sm:p-10">
        <p className="mb-3 text-sm font-semibold uppercase tracking-wider text-brand">{t("home.kicker")}</p>
        <h1 className="max-w-2xl text-3xl font-bold sm:text-4xl">{t("home.title")}</h1>
        <p className="mt-3 max-w-2xl text-lg text-slate-700">{t("home.intro")}</p>
      </section>
      <ol aria-label={t("home.how")} className="grid gap-4 text-sm sm:grid-cols-3">
        {steps.map(([n, title, text]) =>
          <li key={n} className="rounded-xl border border-slate-200 bg-white p-5"><span className="text-xs font-bold text-brand">{n}</span><h2 className="mt-2 font-semibold">{t(title)}</h2><p className="mt-1 text-slate-600">{t(text)}</p></li>)}
      </ol>
      <h2 className="text-xl font-semibold">{t("home.choose")}</h2>
      <div className="grid gap-4 sm:grid-cols-2">
        {professions.map(({ href, key }) => {
          const title = t(`home.${key}`);
          return (
            <Link key={href} href={href}
              className="block rounded-lg border border-slate-200 bg-white p-6 shadow-sm transition hover:border-brand hover:shadow">
              <h2 className="text-xl font-semibold text-brand">{title}</h2>
              <p className="text-sm font-medium text-slate-600">{t(`home.${key}Regulator`)}</p>
              <p className="mt-3 text-slate-700">{t(`home.${key}Text`)}</p>
              <span className="mt-4 inline-block font-medium text-brand">{t("home.start", { name: title.toLowerCase() })}</span>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
