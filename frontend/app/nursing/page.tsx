"use client";

import { useState } from "react";
import { Choice, NumberQuestion, YesNo, answered } from "@/components/Questions";
import RoadmapView from "@/components/RoadmapView";
import { fetchRoadmap } from "@/lib/api";
import type { Roadmap } from "@/lib/types";

type Report = "nnas" | "eca" | "none";
type Rating = "comparable" | "somewhat comparable" | "not comparable";
type Test = "IELTS Academic" | "CELBAN";
const PARTS = ["listening", "reading", "writing", "speaking", "overall"] as const;

export default function Nursing() {
  const [a, setA] = useState({
    nclex_passed: null as boolean | null,
    credential_report: null as Report | null,
    nnas_rating: null as Rating | null,
    practice_hours_last_2_years: null as number | null,
    practice_hours_last_5_years: null as number | null,
    qualifying_program_last_5_years: null as boolean | null,
    english_exemption: null as boolean | null,
    criminal_record_check_done: null as boolean | null,
    jurisprudence_done: null as boolean | null,
    sexual_abuse_course_done: null as boolean | null,
    liability_protection: null as boolean | null,
  });
  const [test, setTest] = useState<Test | null>(null);
  const [takenOn, setTakenOn] = useState("");
  const [scores, setScores] = useState<Record<string, string>>({});
  const [roadmap, setRoadmap] = useState<Roadmap | null>(null);
  const [error, setError] = useState<string | null>(null);
  const set = <K extends keyof typeof a>(key: K) => (value: (typeof a)[K]) => setA((s) => ({ ...s, [key]: value }));

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    const parts = test === "CELBAN" ? PARTS.filter((p) => p !== "overall") : PARTS;
    const english = test && takenOn
      ? { test, taken_on: takenOn, scores: Object.fromEntries(parts.filter((p) => scores[p]).map((p) => [p, Number(scores[p])])) }
      : null;
    try {
      setRoadmap(await fetchRoadmap("crna", { ...answered(a), ...(english ? { english } : {}) }));
    } catch (e) {
      setError((e as Error).message);
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold">Registered nursing in Alberta (CRNA)</h1>
        <p className="mt-2 text-slate-700">Answer what you can. &ldquo;Not sure&rdquo; is fine: the roadmap will tell you what to find out.</p>
      </div>
      <form onSubmit={submit} className="divide-y divide-slate-100 rounded-lg border border-slate-200 bg-white px-5 py-2">
        <YesNo label="Have you passed the NCLEX-RN?" value={a.nclex_passed} onChange={set("nclex_passed")} />
        <Choice label="Which report assesses your nursing education?" value={a.credential_report}
          options={[["nnas", "NNAS advisory report"], ["eca", "Education credential assessment (IQAS, WES, ICAS, ICES or U of T)"], ["none", "None yet"]]}
          onChange={set("credential_report")} />
        {a.credential_report === "nnas" && (
          <Choice label="How did NNAS rate your education?" value={a.nnas_rating}
            options={[["comparable", "Comparable"], ["somewhat comparable", "Somewhat comparable"], ["not comparable", "Not comparable"]]}
            onChange={set("nnas_rating")} />
        )}
        <NumberQuestion label="Nursing practice hours in the last 2 years" unit="hours" hint="RN or NP hours while you held a permit. LPN hours don't count."
          value={a.practice_hours_last_2_years} onChange={set("practice_hours_last_2_years")} />
        <NumberQuestion label="Nursing practice hours in the last 5 years" unit="hours"
          value={a.practice_hours_last_5_years} onChange={set("practice_hours_last_5_years")} />
        <YesNo label="Have you completed a nursing, bridging, re-entry or competence assessment program in the last 5 years?"
          value={a.qualifying_program_last_5_years} onChange={set("qualifying_program_last_5_years")} />
        <fieldset className="py-3">
          <legend className="font-medium">English test results</legend>
          <p className="text-sm text-slate-600">IELTS Academic or CELBAN, taken in the last two years. Leave blank if you have none.</p>
          <div className="mt-2 flex flex-wrap gap-3">
            <Choice label="Test" emptyLabel="No test yet" value={test} options={[["IELTS Academic", "IELTS Academic"], ["CELBAN", "CELBAN"]]} onChange={setTest} />
            {test && (
              <div className="py-3">
                <label htmlFor="taken" className="font-medium">Date taken</label>
                <input id="taken" type="date" value={takenOn} onChange={(e) => setTakenOn(e.target.value)}
                  className="mt-2 block rounded border border-slate-300 px-2 py-1.5" />
              </div>
            )}
          </div>
          {test && (
            <div className="flex flex-wrap gap-3">
              {(test === "CELBAN" ? PARTS.filter((p) => p !== "overall") : PARTS).map((p) => (
                <div key={p}>
                  <label htmlFor={`score-${p}`} className="block text-sm capitalize">{p}</label>
                  <input id={`score-${p}`} type="number" step="0.5" min={0} max={12} value={scores[p] ?? ""}
                    onChange={(e) => setScores((s) => ({ ...s, [p]: e.target.value }))}
                    className="w-20 rounded border border-slate-300 px-2 py-1" />
                </div>
              ))}
            </div>
          )}
        </fieldset>
        {!test && (
          <YesNo label="Does an English exemption apply to you?"
            hint="For example, a nursing program of at least two years taught in English, or 250 practice hours in English in the last five years."
            value={a.english_exemption} onChange={set("english_exemption")} />
        )}
        <YesNo label="Have you completed the criminal record check?" value={a.criminal_record_check_done} onChange={set("criminal_record_check_done")} />
        <YesNo label="Have you completed the Alberta Jurisprudence course?" value={a.jurisprudence_done} onChange={set("jurisprudence_done")} />
        <YesNo label="Have you completed the Protecting Patients from Sexual Abuse and Misconduct course?" value={a.sexual_abuse_course_done} onChange={set("sexual_abuse_course_done")} />
        <YesNo label="Do you have professional liability protection (CNPS)?" value={a.liability_protection} onChange={set("liability_protection")} />
        <div className="py-4">
          <button type="submit" className="rounded bg-brand px-4 py-2 font-medium text-white hover:bg-brand-dark">Show my roadmap</button>
        </div>
      </form>
      {error && <p role="alert" className="rounded bg-rose-50 p-3 text-rose-900">{error}</p>}
      {roadmap && <RoadmapView roadmap={roadmap} />}
    </div>
  );
}
