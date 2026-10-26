"use client";

import { DraftControls, ResultStatus, SectionNav } from "@/components/PlanTools";
import { useReport } from "@/lib/useReport";
import { isRecord, useDraft } from "@/lib/useDraft";
import { Choice, NumberQuestion, YesNo, answered } from "@/components/Questions";
import RoadmapView from "@/components/RoadmapView";
import { fetchRoadmap } from "@/lib/api";
import type { Roadmap } from "@/lib/types";

type Report = "nnas" | "eca" | "none";
type Rating = "comparable" | "somewhat comparable" | "not comparable";
type Test = "IELTS Academic" | "CELBAN";
const PARTS = ["listening", "reading", "writing", "speaking", "overall"] as const;

const emptyAnswers = {
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
  };
const emptyDraft = { answers: emptyAnswers, test: null as Test | null, takenOn: "", scores: {} as Record<string, string> };
function validDraft(v: unknown) {
  if (!isRecord(v) || !isRecord(v.answers) || !isRecord(v.scores) || typeof v.takenOn !== "string" ||
      !(v.test === null || v.test === "IELTS Academic" || v.test === "CELBAN")) return false;
  const answers = v.answers;
  if (Object.keys(answers).length !== Object.keys(emptyAnswers).length) return false;
  return Object.keys(emptyAnswers).every(k => {
    const value = answers[k];
    if (k.startsWith("practice_hours")) return value === null || typeof value === "number" && Number.isInteger(value) && value >= 0;
    if (k === "credential_report") return value === null || ["nnas", "eca", "none"].includes(String(value));
    if (k === "nnas_rating") return value === null || ["comparable", "somewhat comparable", "not comparable"].includes(String(value));
    return value === null || typeof value === "boolean";
  }) && Object.entries(v.scores).every(([k, value]) => PARTS.includes(k as typeof PARTS[number]) && typeof value === "string");
}

export default function Nursing() {
  const draft = useDraft("navigator-nursing-v1", emptyDraft, validDraft);
  const { answers: a, test, takenOn, scores } = draft.value;
  const report = useReport<Roadmap>();
  function update(change: Partial<typeof emptyDraft>) { report.invalidate(); draft.setValue(s => ({ ...s, ...change })); }
  const set = <K extends keyof typeof a>(key: K) => (value: (typeof a)[K]) => {
    report.invalidate();
    draft.setValue(s => ({ ...s, answers: { ...s.answers, [key]: value,
      ...(key === "credential_report" && value !== "nnas" ? { nnas_rating: null } : {}) } }));
  };
  function setTest(value: Test | null) {
    report.invalidate();
    draft.setValue(s => ({ ...s, test: value, takenOn: "", scores: {}, answers: { ...s.answers, english_exemption: null } }));
  }
  async function submit(event: React.FormEvent) {
    event.preventDefault();
    const parts = test === "CELBAN" ? PARTS.filter(p => p !== "overall") : PARTS;
    const english = test && takenOn ? { test, taken_on: takenOn,
      scores: Object.fromEntries(parts.filter(p => scores[p] !== undefined && scores[p] !== "").map(p => [p, Number(scores[p])])) } : null;
    const { english_exemption, nnas_rating, ...rest } = a;
    const payload = { ...answered(rest), ...(a.credential_report === "nnas" ? { nnas_rating } : {}),
      ...(english ? { english } : { english_exemption }) };
    await report.run(signal => fetchRoadmap("crna", payload, signal));
  }

  return (
    <div className="space-y-7">
      <div>
        <h1 className="text-3xl font-bold">Registered nursing in Alberta (CRNA)</h1>
        <p className="mt-2 text-slate-700">Answer what you can. &ldquo;Not sure&rdquo; is fine: the roadmap will tell you what to find out.</p>
      </div>
      <SectionNav sections={[["education", "Education"], ["practice", "Practice"], ["english", "English"], ["checks", "Final checks"], ...(report.result ? [["roadmap-title", "Roadmap"], ["costs", "Costs"]] as [string,string][] : [])]} />
      <DraftControls enabled={draft.enabled} toggle={draft.toggle} notice={draft.notice} />
      <form onSubmit={submit} className="divide-y divide-slate-100 rounded-lg border border-slate-200 bg-white px-5 py-2">
        <section id="education" className="form-section" aria-labelledby="education-heading"><h2 id="education-heading">1. Your education</h2>
        <YesNo label="Have you passed the NCLEX-RN?" value={a.nclex_passed} onChange={set("nclex_passed")} />
        <Choice label="Which report assesses your nursing education?" value={a.credential_report}
          options={[["nnas", "NNAS advisory report"], ["eca", "Education credential assessment (IQAS, WES, ICAS, ICES or U of T)"], ["none", "None yet"]]}
          onChange={set("credential_report")} />
        {a.credential_report === "nnas" && (
          <Choice label="How did NNAS rate your education?" value={a.nnas_rating}
            options={[["comparable", "Comparable"], ["somewhat comparable", "Somewhat comparable"], ["not comparable", "Not comparable"]]}
            onChange={set("nnas_rating")} />
        )}
        </section>
        <section id="practice" className="form-section" aria-labelledby="practice-heading"><h2 id="practice-heading">2. Recent practice</h2>
        <NumberQuestion label="Nursing practice hours in the last 2 years" unit="hours" hint="RN or NP hours while you held a permit. LPN hours don't count."
          value={a.practice_hours_last_2_years} onChange={set("practice_hours_last_2_years")} />
        <NumberQuestion label="Nursing practice hours in the last 5 years" unit="hours"
          value={a.practice_hours_last_5_years} onChange={set("practice_hours_last_5_years")} />
        <YesNo label="Have you completed a nursing, bridging, re-entry or competence assessment program in the last 5 years?"
          value={a.qualifying_program_last_5_years} onChange={set("qualifying_program_last_5_years")} />
        </section>
        <section id="english" className="form-section" aria-labelledby="english-heading"><h2 id="english-heading">3. English evidence</h2>
        <fieldset className="py-3">
          <legend className="font-medium">English test results</legend>
          <p className="text-sm text-slate-600">IELTS Academic or CELBAN, taken in the last two years. Leave blank if you have none.</p>
          <div className="mt-2 flex flex-wrap gap-3">
            <Choice label="Test" emptyLabel="No test yet" value={test} options={[["IELTS Academic", "IELTS Academic"], ["CELBAN", "CELBAN"]]} onChange={setTest} />
            {test && (
              <div className="py-3">
                <label htmlFor="taken" className="font-medium">Date taken</label>
                <input id="taken" type="date" required max={new Date().toLocaleDateString("en-CA")} aria-describedby="date-help" value={takenOn} onChange={(e) => update({ takenOn: e.target.value })}
                  className="mt-2 block rounded border border-slate-300 px-2 py-1.5" />
                <p id="date-help" className="mt-1 text-sm text-slate-600">Date required for test results. Future dates cannot be used.</p>
              </div>
            )}
          </div>
          {test && <p className="mb-2 text-sm text-slate-600">Using {test} results. Any earlier exemption answer has been cleared. Leave unknown scores blank; the roadmap will identify missing scores.</p>}
          {test && (
            <div className="flex flex-wrap gap-3">
              {(test === "CELBAN" ? PARTS.filter((p) => p !== "overall") : PARTS).map((p) => (
                <div key={p}>
                  <label htmlFor={`score-${p}`} className="block text-sm capitalize">{p}</label>
                  <input id={`score-${p}`} type="number" step={test === "IELTS Academic" ? 0.5 : 1} min={0} max={test === "IELTS Academic" ? 9 : 12} value={scores[p] ?? ""}
                    onChange={(e) => update({ scores: { ...scores, [p]: e.target.value } })}
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
        </section>
        <section id="checks" className="form-section" aria-labelledby="checks-heading"><h2 id="checks-heading">4. Final checks</h2>
        <YesNo label="Have you completed the criminal record check?" value={a.criminal_record_check_done} onChange={set("criminal_record_check_done")} />
        <YesNo label="Have you completed the Alberta Jurisprudence course?" value={a.jurisprudence_done} onChange={set("jurisprudence_done")} />
        <YesNo label="Have you completed the Protecting Patients from Sexual Abuse and Misconduct course?" value={a.sexual_abuse_course_done} onChange={set("sexual_abuse_course_done")} />
        <YesNo label="Do you have professional liability protection (CNPS)?" value={a.liability_protection} onChange={set("liability_protection")} />
        </section>
        <div className="py-5">
          <button type="submit" disabled={report.busy} className="rounded-lg bg-brand px-5 py-3 font-semibold text-white hover:bg-brand-dark disabled:opacity-60">{report.busy ? "Building your roadmap…" : "Show my roadmap"}</button>
          <p className="mt-2 text-sm text-slate-600">Editing an answer clears the previous roadmap.</p>
        </div>
      </form>
      <ResultStatus busy={report.busy} ready={!!report.result} />
      {report.error && <p role="alert" className="rounded bg-rose-50 p-3 text-rose-900">{report.error}</p>}
      {report.result && <RoadmapView roadmap={report.result} />}
    </div>
  );
}
