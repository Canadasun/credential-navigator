"use client";

import DocumentUploader from "@/components/DocumentUploader";
import { NumberQuestion, YesNo, answered } from "@/components/Questions";
import RoadmapView from "@/components/RoadmapView";
import { DraftControls, ResultStatus, SectionNav } from "@/components/PlanTools";
import { fetchRoadmap } from "@/lib/api";
import { useReport } from "@/lib/useReport";
import { isRecord, useDraft } from "@/lib/useDraft";
import type { Roadmap } from "@/lib/types";

const empty = {
  experience_months: null as number | null,
  canadian_citizen_or_pr: null as boolean | null,
  ceab_accredited_degree: null as boolean | null,
  wes_icap_received: null as boolean | null,
  nppe_passed: null as boolean | null,
  english_competent: null as boolean | null,
  references_ready: null as boolean | null,
};
function validDraft(v: unknown) {
  return isRecord(v) && Object.keys(v).length === Object.keys(empty).length && Object.keys(empty).every(k =>
    k === "experience_months" ? v[k] === null || typeof v[k] === "number" && Number.isInteger(v[k]) && (v[k] as number) >= 0 && (v[k] as number) <= 720 : v[k] === null || typeof v[k] === "boolean");
}

export default function Engineering() {
  const draft = useDraft("navigator-engineering-v1", empty, validDraft);
  const answers = draft.value;
  const report = useReport<Roadmap>();
  const set = <K extends keyof typeof empty>(key: K) => (value: (typeof empty)[K]) => {
    report.invalidate(); draft.setValue(a => ({ ...a, [key]: value }));
  };
  async function submit(event: React.FormEvent) {
    event.preventDefault();
    await report.run(signal => fetchRoadmap("apega", answered(answers), signal));
  }
  return <div className="space-y-7">
    <div><p className="mb-2 text-sm font-semibold uppercase tracking-wider text-brand">Your licensing plan · Engineering</p>
      <h1 className="text-3xl font-bold">Engineering in Alberta (APEGA)</h1>
      <p className="mt-2 max-w-2xl text-slate-700">Answer what you can. &ldquo;Not sure&rdquo; is fine: your roadmap will tell you what to find out.</p></div>
    <SectionNav sections={[["profile", "Your profile"], ["readiness", "Readiness"], ...(report.result ? [["roadmap-title", "Roadmap"], ["costs", "Costs"]] as [string,string][] : []), ["gap-title", "Course comparison"]]} />
    <DraftControls enabled={draft.enabled} toggle={draft.toggle} notice={draft.notice} />
    <form onSubmit={submit} className="rounded-xl border border-slate-200 bg-white px-5">
      <section id="profile" className="form-section" aria-labelledby="profile-heading"><h2 id="profile-heading">1. Your background</h2>
        <NumberQuestion label="How many months of engineering work experience do you have?" unit="months" max={720}
          hint="Count experience after your degree, in Canada or abroad." value={answers.experience_months} onChange={set("experience_months")} />
        <YesNo label="Are you a Canadian citizen or permanent resident?" value={answers.canadian_citizen_or_pr} onChange={set("canadian_citizen_or_pr")} />
        <YesNo label="Is your degree from a CEAB-accredited program?" hint="Most degrees from outside Canada are not."
          value={answers.ceab_accredited_degree} onChange={set("ceab_accredited_degree")} />
      </section>
      <section id="readiness" className="form-section" aria-labelledby="readiness-heading"><h2 id="readiness-heading">2. Documents and readiness</h2>
        <YesNo label="Has WES sent your Course-by-Course ICAP report to APEGA?" value={answers.wes_icap_received} onChange={set("wes_icap_received")} />
        <YesNo label="Have you passed the National Professional Practice Exam (NPPE)?" value={answers.nppe_passed} onChange={set("nppe_passed")} />
        <YesNo label="Are you comfortable communicating professionally in English?" value={answers.english_competent} onChange={set("english_competent")} />
        <YesNo label="Do you have references who can confirm your experience?" value={answers.references_ready} onChange={set("references_ready")} />
      </section>
      <div className="py-5"><button type="submit" disabled={report.busy} className="rounded-lg bg-brand px-5 py-3 font-semibold text-white hover:bg-brand-dark disabled:opacity-60">{report.busy ? "Building your roadmap…" : "Show my roadmap"}</button>
        <p className="mt-2 text-sm text-slate-600">Results reflect these answers. Editing an answer clears the previous roadmap.</p></div>
    </form>
    <ResultStatus busy={report.busy} ready={!!report.result} />
    {report.error && <p role="alert" className="rounded bg-rose-50 p-3 text-rose-900">{report.error}</p>}
    {report.result && <RoadmapView roadmap={report.result} />}
    <DocumentUploader />
  </div>;
}
