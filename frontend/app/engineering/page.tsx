"use client";

import { useState } from "react";
import DocumentUploader from "@/components/DocumentUploader";
import { NumberQuestion, YesNo, answered } from "@/components/Questions";
import RoadmapView from "@/components/RoadmapView";
import { fetchRoadmap } from "@/lib/api";
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

export default function Engineering() {
  const [answers, setAnswers] = useState(empty);
  const [roadmap, setRoadmap] = useState<Roadmap | null>(null);
  const [error, setError] = useState<string | null>(null);
  const set = <K extends keyof typeof empty>(key: K) => (value: (typeof empty)[K]) =>
    setAnswers((a) => ({ ...a, [key]: value }));

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    try {
      setRoadmap(await fetchRoadmap("apega", answered(answers)));
    } catch (e) {
      setError((e as Error).message);
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold">Engineering in Alberta (APEGA)</h1>
        <p className="mt-2 text-slate-700">Answer what you can. &ldquo;Not sure&rdquo; is fine: the roadmap will tell you what to find out.</p>
      </div>
      <form onSubmit={submit} className="divide-y divide-slate-100 rounded-lg border border-slate-200 bg-white px-5 py-2">
        <NumberQuestion label="How many months of engineering work experience do you have?" unit="months" max={720}
          hint="Count experience after your degree, in Canada or abroad." value={answers.experience_months} onChange={set("experience_months")} />
        <YesNo label="Are you a Canadian citizen or permanent resident?" value={answers.canadian_citizen_or_pr} onChange={set("canadian_citizen_or_pr")} />
        <YesNo label="Is your degree from a CEAB-accredited program?" hint="Most degrees from outside Canada are not."
          value={answers.ceab_accredited_degree} onChange={set("ceab_accredited_degree")} />
        <YesNo label="Has WES sent your Course-by-Course ICAP report to APEGA?" value={answers.wes_icap_received} onChange={set("wes_icap_received")} />
        <YesNo label="Have you passed the National Professional Practice Exam (NPPE)?" value={answers.nppe_passed} onChange={set("nppe_passed")} />
        <YesNo label="Are you comfortable communicating professionally in English?" value={answers.english_competent} onChange={set("english_competent")} />
        <YesNo label="Do you have references who can confirm your experience?" value={answers.references_ready} onChange={set("references_ready")} />
        <div className="py-4">
          <button type="submit" className="rounded bg-brand px-4 py-2 font-medium text-white hover:bg-brand-dark">Show my roadmap</button>
        </div>
      </form>
      {error && <p role="alert" className="rounded bg-rose-50 p-3 text-rose-900">{error}</p>}
      {roadmap && <RoadmapView roadmap={roadmap} />}
      <DocumentUploader />
    </div>
  );
}
