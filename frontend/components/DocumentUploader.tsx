"use client";

import { useEffect, useId, useState } from "react";
import { useReport } from "@/lib/useReport";
import { ExportTools, ResultStatus } from "./PlanTools";
import { analyseDocument, fetchDisciplines } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import type { Discipline, GapAnalysis } from "@/lib/types";

const STYLES = { likely_covered: "text-emerald-800", partial: "text-amber-800", possible_gap: "text-rose-800" };

export default function DocumentUploader() {
  const [disciplines, setDisciplines] = useState<Discipline[]>([]);
  const [discipline, setDiscipline] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const report = useReport<{ analysis: GapAnalysis; filename: string; disciplineName: string }>();
  const { result, busy } = report;
  const [loadError, setLoadError] = useState<string | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);
  const [retry, setRetry] = useState(0);
  const fileId = useId();
  const disciplineId = useId();
  const { t } = useI18n();

  useEffect(() => {
    let active = true;
    setLoadError(null);
    fetchDisciplines().then(data => { if (active) setDisciplines(data); })
      .catch((e: Error) => { if (active) setLoadError(e.message); });
    return () => { active = false; };
  }, [retry]);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (!file || !discipline || fileError) return;
    await report.run(async signal => ({ analysis: await analyseDocument(discipline, file, signal),
      filename: file.name, disciplineName: disciplines.find(d => d.id === discipline)?.name || discipline }));
  }

  return (
    <section aria-labelledby="gap-title" className="rounded-lg border border-slate-200 bg-white p-5">
      <h2 id="gap-title" className="text-2xl font-semibold">{t("gap.title")}</h2>
      <p className="mt-2 text-slate-700">{t("gap.intro")}</p>
      {loadError && <div role="alert" className="mt-4 rounded bg-rose-50 p-3 text-rose-900">{loadError} <button type="button" className="underline" onClick={() => setRetry(n => n + 1)}>{t("gap.retry")}</button></div>}
      <form onSubmit={submit} className="mt-4 flex min-w-0 flex-wrap items-end gap-4">
        <div className="w-full min-w-0 sm:w-auto sm:max-w-full">
          <label htmlFor={disciplineId} className="block font-medium">{t("gap.discipline")}</label>
          <select id={disciplineId} required value={discipline} onChange={(e) => { report.invalidate(); setDiscipline(e.target.value); }}
            className="mt-1 w-full max-w-full rounded border border-slate-300 bg-white px-2 py-1.5">
            <option value="">{t("gap.choose")}</option>
            {disciplines.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
          </select>
        </div>
        <div className="w-full min-w-0 sm:w-auto sm:flex-1">
          <label htmlFor={fileId} className="block font-medium">{t("gap.file")}</label>
          <input id={fileId} type="file" accept="application/pdf" required
            onChange={(e) => {
              report.invalidate(); const next = e.target.files?.[0] ?? null; setFile(next);
              setFileError(next && next.size > 10 * 1024 * 1024 ? t("gap.tooLarge") : null);
            }} className="mt-1 block w-full min-w-0 max-w-full text-sm" />
        </div>
        <button type="submit" disabled={busy || !file || !discipline || !!fileError}
          className="rounded bg-brand px-4 py-2 font-medium text-white hover:bg-brand-dark disabled:opacity-50">
          {busy ? t("gap.reading") : t("gap.compare")}
        </button>
      </form>
      <p className="mt-2 text-sm text-slate-600">{t("gap.help")}</p>
      <ResultStatus busy={busy} ready={!!result} id="gap-results-title" label={t("gap.label")} />
      {(fileError || report.error) && <p role="alert" className="mt-4 rounded bg-rose-50 p-3 text-rose-900">{fileError || report.error}</p>}
      {result && <div className="mt-6 space-y-3">
        <h3 id="gap-results-title" tabIndex={-1} className="text-xl font-semibold">{t("gap.results")}</h3>
        <p className="text-sm text-slate-600">{t("gap.document")} <strong>{result.filename}</strong> · {t("gap.disciplineLabel")} <strong>{result.disciplineName}</strong></p>
        <ExportTools value={result} filename="credential-navigator-course-comparison.json" />
        <GapReport result={result.analysis} />
      </div>}
    </section>
  );
}

function GapReport({ result }: { result: GapAnalysis }) {
  const s = result.summary;
  const { lang, t } = useI18n();
  const english = lang === "fr" ? "en" : undefined;
  return (
    <div className="mt-6 space-y-4">
      {lang === "fr" ? (
        <p className="text-lg">
          Nous avons trouvé <strong>{s.courses_found} cours</strong>. Sur <strong>{s.exams_required}</strong> examens
          exigés, <strong>{s.likely_covered}</strong> semblent couverts et <strong>{s.possibly_needed}</strong> pourraient
          encore être exigés.
        </p>
      ) : (
        <p className="text-lg">
          We found <strong>{s.courses_found} courses</strong>. Of <strong>{s.exams_required}</strong> exam requirements,{" "}
          <strong>{s.likely_covered}</strong> look covered and <strong>{s.possibly_needed}</strong> may still be needed.
        </p>
      )}
      {result.notes.length > 0 && (
        <ul className="list-disc space-y-1 rounded bg-amber-50 p-3 pl-8 text-sm text-amber-900" lang={english}>
          {result.notes.map((n) => <li key={n}>{n}</li>)}
        </ul>
      )}
      {result.groups.map((g) => (
        <div key={g.name} className="rounded border border-slate-200">
          <h3 className="flex flex-wrap justify-between gap-2 bg-slate-50 px-3 py-2 font-semibold">
            <span><span lang={english}>{g.name}</span> <span className="font-normal text-slate-600">{t("gap.required", { n: g.required })}</span></span>
            <span className={g.possibly_needed ? "text-rose-800" : "text-emerald-800"}>
              {g.possibly_needed ? t("gap.mayBeNeeded", { n: g.possibly_needed }) : t("gap.covered")}
            </span>
          </h3>
          <ul className="divide-y divide-slate-100 text-sm">
            {g.exams.map((m) => (
              <li key={m.exam.code} className="flex flex-wrap justify-between gap-2 px-3 py-2">
                <span><span className="font-mono text-xs text-slate-600">{m.exam.code}</span> <span lang={english}>{m.exam.title}</span></span>
                <span className={STYLES[m.status]}>
                  {t(`gap.${m.status}`)}
                  {m.best_course && <span className="text-slate-600"> · {m.best_course.code} {m.best_course.title}</span>}
                </span>
                {m.best_course && <details className="w-full text-slate-600">
                  <summary className="cursor-pointer font-medium text-brand">{t("gap.why")}</summary>
                  <p className="mt-1">{t("gap.shared", { terms: m.shared_terms.length ? m.shared_terms.join(", ") : t("gap.noShared") })}</p>
                </details>}
              </li>
            ))}
          </ul>
        </div>
      ))}
      <details className="text-sm">
        <summary className="cursor-pointer font-medium">{t("gap.courses")}</summary>
        <ul className="mt-2 space-y-1">
          {result.courses_found.map((c) => (
            <li key={c.code}><span className="font-mono">{c.code}</span> {c.title}{c.grade ? ` (${c.grade})` : ""}</li>
          ))}
        </ul>
      </details>
      <p className="text-sm text-slate-600"><span lang={english}>{result.disclaimer}</span>{" "}
        {result.syllabus_source && <a href={result.syllabus_source} target="_blank" rel="noreferrer" className="underline">{t("gap.syllabus")}</a>}
      </p>
    </div>
  );
}
