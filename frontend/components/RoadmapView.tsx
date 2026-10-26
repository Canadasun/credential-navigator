"use client";
import { ExportTools } from "./PlanTools";
import { money } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import type { Roadmap, Status } from "@/lib/types";

const STYLES: Record<Status, string> = {
  done: "bg-emerald-100 text-emerald-900",
  to_do: "bg-sky-100 text-sky-900",
  to_confirm: "bg-amber-100 text-amber-900",
  may_apply: "bg-violet-100 text-violet-900",
  not_needed: "bg-slate-100 text-slate-700",
};

export default function RoadmapView({ roadmap }: { roadmap: Roadmap }) {
  const { lang, t } = useI18n();
  const counted = roadmap.requirements.filter((r) => r.status !== "not_needed" && r.status !== "may_apply");
  const done = counted.filter((r) => r.status === "done").length;
  const totals = (values?: Record<string, number>) => values
    ? Object.entries(values).map(([currency, amount]) => money(amount, currency, lang)).join(" + ")
    : t("roadmap.none");
  // Regulator facts and advice come from the API in English; marking them lets screen readers pronounce them.
  const sourceLanguage = lang === "fr" ? "en" : undefined;
  return (
    <section aria-labelledby="roadmap-title" className="space-y-6">
      <div className="rounded-lg border border-slate-200 bg-white p-5">
        <h2 id="roadmap-title" tabIndex={-1} className="text-2xl font-semibold">{t("roadmap.title")}</h2>
        {t("roadmap.englishOnly") && <p className="mt-2 rounded bg-sky-50 p-3 text-sm text-sky-900">{t("roadmap.englishOnly")}</p>}
        {roadmap.pathway ? (
          <p className="mt-2"><span className="font-medium">{t("roadmap.route", { name: roadmap.pathway.name })}</span>{" "}
            <span lang={sourceLanguage}>{roadmap.pathway.summary}</span></p>
        ) : (
          <p className="mt-2 text-amber-900" lang={sourceLanguage}>{roadmap.pathway_note}</p>
        )}
        <div className="mt-4">
          <div className="flex justify-between text-sm"><span>{t("roadmap.progress", { done, total: counted.length })}</span></div>
          <div className="mt-1 h-3 rounded bg-slate-200" role="progressbar" aria-valuemin={0}
            aria-valuemax={counted.length} aria-valuenow={done} aria-label={t("roadmap.progressLabel")}>
            <div className="h-3 rounded bg-emerald-600" style={{ width: `${counted.length ? (100 * done) / counted.length : 0}%` }} />
          </div>
        </div>
      </div>

      <ExportTools value={roadmap} filename="credential-navigator-roadmap.json" />
      {roadmap.next_steps.length > 0 && (
        <div className="rounded-lg border border-slate-200 bg-white p-5">
          <h3 className="text-lg font-semibold">{t("roadmap.nextSteps")}</h3>
          <ol className="mt-2 list-decimal space-y-1 pl-5" lang={sourceLanguage}>
            {roadmap.next_steps.map((step) => <li key={step}>{step}</li>)}
          </ol>
        </div>
      )}

      <div className="rounded-lg border border-slate-200 bg-white p-5">
        <h3 id="requirements" className="text-lg font-semibold">{t("roadmap.requirements")}</h3>
        <ul className="mt-2 divide-y divide-slate-100">
          {roadmap.requirements.map((r) => (
            <li key={r.id} className="py-3">
              <div className="flex flex-wrap items-center gap-2">
                <span className={`rounded px-2 py-0.5 text-xs font-semibold ${STYLES[r.status]}`}>{t(`label.${r.status}`)}</span>
                <span className="font-medium" lang={sourceLanguage}>{r.title}</span>
                {r.stage && <span className="rounded border border-slate-300 px-2 py-0.5 text-xs text-slate-700">{t(`roadmap.stage.${r.stage}`)}</span>}
              </div>
              {r.detail && <p className="mt-1 text-sm" lang={sourceLanguage}>{r.detail}</p>}
              <p className="mt-1 text-sm text-slate-600">
                <span lang={sourceLanguage}>{r.description}</span>{" "}
                <a href={r.source_url} target="_blank" rel="noreferrer" className="text-brand underline">{t("roadmap.source")}</a>
              </p>
            </li>
          ))}
        </ul>
      </div>

      <div className="rounded-lg border border-slate-200 bg-white p-5">
        <h3 id="costs" className="text-lg font-semibold">{t("roadmap.costs")}</h3>
        <p className="mt-1">{t("roadmap.expected")} <strong>{totals(roadmap.cost_totals.expected)}</strong></p>
        <p className="text-sm text-slate-600">{t("roadmap.possible")} {totals(roadmap.cost_totals.possible)}</p>
        <div className="mt-3 overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead><tr className="border-b text-slate-600"><th className="py-1 pr-3">{t("roadmap.fee")}</th><th className="pr-3">{t("roadmap.paidTo")}</th><th className="pr-3">{t("roadmap.amount")}</th><th>{t("roadmap.when")}</th></tr></thead>
            <tbody>
              {roadmap.costs.map((c) => (
                <tr key={c.name} className="border-b border-slate-100 align-top">
                  <td className="py-2 pr-3" lang={sourceLanguage}><a href={c.source_url} target="_blank" rel="noreferrer" className="underline">{c.name}</a></td>
                  <td className="pr-3">{c.payee}</td>
                  <td className="pr-3 whitespace-nowrap">{money(c.amount, c.currency, lang)}{c.gst === "excluded" ? t("roadmap.plusGst") : ""}{c.gst === "not_stated" ? t("roadmap.taxNotStated") : ""}</td>
                  <td>{c.status === "may_apply" ? t("roadmap.onlyIfNeeded") : ""}<span lang={sourceLanguage}>{c.note}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <ul className="mt-3 list-disc pl-5 text-sm text-slate-600" lang={sourceLanguage}>
          {roadmap.cost_notes.map((n) => <li key={n}>{n}</li>)}
        </ul>
      </div>

      <div className="rounded-lg border border-slate-200 bg-white p-5">
        <h3 id="timelines" className="text-lg font-semibold">{t("roadmap.timelines")}</h3>
        <ul className="mt-2 space-y-1 text-sm">
          {roadmap.timelines.map((item) => (
            <li key={item.name}>
              <span className="font-medium" lang={sourceLanguage}>{item.name}</span>
              {item.max_days && t(item.business_days ? "roadmap.upToBusiness" : "roadmap.upTo", { days: item.max_days })}
              {item.description && <span lang={sourceLanguage}>. {item.description}</span>}{" "}
              {item.source_url && <a href={item.source_url} target="_blank" rel="noreferrer" className="text-brand underline">{t("roadmap.timelineSource")}<span className="sr-only">: {item.name}</span></a>}
            </li>
          ))}
        </ul>
      </div>
      <p className="text-sm text-slate-600" lang={sourceLanguage}>{roadmap.disclaimer}</p>
    </section>
  );
}
