"use client";

import { useEffect, useId, useState } from "react";
import { analyseDocument, fetchDisciplines } from "@/lib/api";
import type { Discipline, GapAnalysis } from "@/lib/types";

const STATUS = {
  likely_covered: { text: "Likely covered", style: "text-emerald-800" },
  partial: { text: "Partly covered: check", style: "text-amber-800" },
  possible_gap: { text: "Possible gap", style: "text-rose-800" },
};

export default function DocumentUploader() {
  const [disciplines, setDisciplines] = useState<Discipline[]>([]);
  const [discipline, setDiscipline] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<GapAnalysis | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const fileId = useId();
  const disciplineId = useId();

  useEffect(() => {
    fetchDisciplines().then(setDisciplines).catch((e: Error) => setError(e.message));
  }, []);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (!file || !discipline) return;
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      setResult(await analyseDocument(discipline, file));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section aria-labelledby="gap-title" className="rounded-lg border border-slate-200 bg-white p-5">
      <h2 id="gap-title" className="text-2xl font-semibold">Compare your courses with APEGA&apos;s syllabus</h2>
      <p className="mt-2 text-slate-700">
        If your degree is not CEAB-accredited, APEGA&apos;s Board of Examiners compares it with its exam syllabus and
        may assign exams. Upload your course descriptions (best) or your transcript as a PDF to see which exams may
        apply. Scanned documents are read on our server; nothing is stored.
      </p>
      <form onSubmit={submit} className="mt-4 flex flex-wrap items-end gap-4">
        <div>
          <label htmlFor={disciplineId} className="block font-medium">Your discipline</label>
          <select id={disciplineId} required value={discipline} onChange={(e) => setDiscipline(e.target.value)}
            className="mt-1 rounded border border-slate-300 bg-white px-2 py-1.5">
            <option value="">Choose…</option>
            {disciplines.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
          </select>
        </div>
        <div>
          <label htmlFor={fileId} className="block font-medium">Course descriptions or transcript (PDF, up to 10 MB)</label>
          <input id={fileId} type="file" accept="application/pdf" required
            onChange={(e) => setFile(e.target.files?.[0] ?? null)} className="mt-1 block text-sm" />
        </div>
        <button type="submit" disabled={busy || !file || !discipline}
          className="rounded bg-brand px-4 py-2 font-medium text-white hover:bg-brand-dark disabled:opacity-50">
          {busy ? "Reading your document…" : "Compare"}
        </button>
      </form>
      <div aria-live="polite">
        {error && <p role="alert" className="mt-4 rounded bg-rose-50 p-3 text-rose-900">{error}</p>}
        {result && <GapReport result={result} />}
      </div>
    </section>
  );
}

function GapReport({ result }: { result: GapAnalysis }) {
  const s = result.summary;
  return (
    <div className="mt-6 space-y-4">
      <p className="text-lg">
        We found <strong>{s.courses_found} courses</strong>. Of <strong>{s.exams_required}</strong> exam requirements,{" "}
        <strong>{s.likely_covered}</strong> look covered and <strong>{s.possibly_needed}</strong> may still be needed.
      </p>
      {result.notes.length > 0 && (
        <ul className="list-disc space-y-1 rounded bg-amber-50 p-3 pl-8 text-sm text-amber-900">
          {result.notes.map((n) => <li key={n}>{n}</li>)}
        </ul>
      )}
      {result.groups.map((g) => (
        <div key={g.name} className="rounded border border-slate-200">
          <h3 className="flex flex-wrap justify-between gap-2 bg-slate-50 px-3 py-2 font-semibold">
            <span>{g.name} <span className="font-normal text-slate-600">({g.required} required)</span></span>
            <span className={g.possibly_needed ? "text-rose-800" : "text-emerald-800"}>
              {g.possibly_needed ? `${g.possibly_needed} may be needed` : "Looks covered"}
            </span>
          </h3>
          <ul className="divide-y divide-slate-100 text-sm">
            {g.exams.map((m) => (
              <li key={m.exam.code} className="flex flex-wrap justify-between gap-2 px-3 py-2">
                <span><span className="font-mono text-xs text-slate-600">{m.exam.code}</span> {m.exam.title}</span>
                <span className={STATUS[m.status].style}>
                  {STATUS[m.status].text}
                  {m.best_course && <span className="text-slate-600"> · {m.best_course.code} {m.best_course.title}</span>}
                </span>
              </li>
            ))}
          </ul>
        </div>
      ))}
      <details className="text-sm">
        <summary className="cursor-pointer font-medium">Courses we read from your document</summary>
        <ul className="mt-2 space-y-1">
          {result.courses_found.map((c) => (
            <li key={c.code}><span className="font-mono">{c.code}</span> {c.title}{c.grade ? ` (${c.grade})` : ""}</li>
          ))}
        </ul>
      </details>
      <p className="text-sm text-slate-600">{result.disclaimer}{" "}
        {result.syllabus_source && <a href={result.syllabus_source} target="_blank" rel="noreferrer" className="underline">APEGA syllabus</a>}
      </p>
    </div>
  );
}
