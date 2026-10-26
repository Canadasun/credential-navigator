"use client";

import Link from "next/link";
import { DraftControls, ResultStatus, SectionNav, SubmitButton } from "@/components/PlanTools";
import { Choice, NumberQuestion, YesNo, answered } from "@/components/Questions";
import RoadmapView from "@/components/RoadmapView";
import { fetchRoadmap } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { useReport } from "@/lib/useReport";
import { isRecord, useDraft } from "@/lib/useDraft";
import type { Roadmap } from "@/lib/types";

const EDUCATION = [
  "non-accredited-4-year-university-cs", "non-accredited-3-year-university-cs", "accredited-4-year-university-cs",
  "accredited-4-year-university-interdisciplinary", "accredited-3-year-university-cs", "accredited-3-year-college",
  "accredited-2-year-college", "non-accredited-3-year-college", "non-accredited-2-year-college",
  "accredited-post-graduate-it", "non-it-or-none",
] as const;
type Education = typeof EDUCATION[number];

const empty = {
  education: null as Education | null,
  it_experience_years: null as number | null,
  sfia_level_3: null as boolean | null,
  hours_last_12_months: null as number | null,
  cips_member: null as boolean | null,
  transcripts_sent: null as boolean | null,
  references_ready: null as boolean | null,
  skills_assessment_done: null as boolean | null,
  recent_graduate: null as boolean | null,
};
function validDraft(v: unknown) {
  return isRecord(v) && Object.keys(v).length === Object.keys(empty).length && Object.keys(empty).every(k => {
    const value = v[k];
    if (k === "education") return value === null || EDUCATION.includes(value as Education);
    if (k === "it_experience_years" || k === "hours_last_12_months") return value === null || typeof value === "number" && value >= 0;
    return value === null || typeof value === "boolean";
  });
}

export default function Computing() {
  const { t } = useI18n();
  const draft = useDraft("navigator-computing-v1", empty, validDraft);
  const answers = draft.value;
  const report = useReport<Roadmap>();
  const set = <K extends keyof typeof empty>(key: K) => (value: (typeof empty)[K]) => {
    report.invalidate(); draft.setValue(a => ({ ...a, [key]: value }));
  };
  async function submit(event: React.FormEvent) {
    event.preventDefault();
    await report.run(signal => fetchRoadmap("cips", answered(answers), signal));
  }
  return <div className="space-y-7">
    <div><p className="mb-2 text-sm font-semibold uppercase tracking-wider text-brand">{t("cs.kicker")}</p>
      <h1 className="text-3xl font-bold">{t("cs.title")}</h1>
      <div className="mt-3 max-w-3xl space-y-2 rounded-lg border border-sky-200 bg-sky-50 p-4 text-slate-800">
        <p>{t("cs.lead")}</p>
        <ul className="list-disc space-y-1 pl-5">
          <li>{t("cs.leadIsp")}</li>
          <li>{t("cs.leadEngineer")} <Link href="/engineering" className="font-medium text-brand underline">{t("cs.engineeringLink")}</Link>.</li>
        </ul>
      </div>
      <p className="mt-3 max-w-2xl text-slate-700">{t("form.intro")}</p></div>
    <SectionNav sections={[["education", t("cs.navEducation")], ["experience", t("cs.navExperience")], ["application", t("cs.navApplication")],
      ...(report.result ? [["roadmap-title", t("form.roadmap")], ["costs", t("form.costs")]] as [string, string][] : [])]} />
    <DraftControls enabled={draft.enabled} toggle={draft.toggle} notice={draft.notice} />
    <form onSubmit={submit} className="rounded-xl border border-slate-200 bg-white px-5">
      <section id="education" className="form-section" aria-labelledby="education-heading"><h2 id="education-heading">{t("cs.s1")}</h2>
        <Choice label={t("cs.education")} hint={t("cs.educationHint")} value={answers.education}
          options={EDUCATION.map((e) => [e, t(`cs.edu.${e}`)] as [Education, string])} onChange={set("education")} />
        <YesNo label={t("cs.recentGraduate")} hint={t("cs.recentGraduateHint")} value={answers.recent_graduate} onChange={set("recent_graduate")} />
      </section>
      <section id="experience" className="form-section" aria-labelledby="experience-heading"><h2 id="experience-heading">{t("cs.s2")}</h2>
        <NumberQuestion label={t("cs.experience")} hint={t("cs.experienceHint")} unit={t("unit.years")} max={60} step={0.5}
          value={answers.it_experience_years} onChange={set("it_experience_years")} />
        <YesNo label={t("cs.sfia")} hint={t("cs.sfiaHint")} value={answers.sfia_level_3} onChange={set("sfia_level_3")} />
        <NumberQuestion label={t("cs.hours")} hint={t("cs.hoursHint")} unit={t("unit.hours")} max={8784}
          value={answers.hours_last_12_months} onChange={set("hours_last_12_months")} />
      </section>
      <section id="application" className="form-section" aria-labelledby="application-heading"><h2 id="application-heading">{t("cs.s3")}</h2>
        <YesNo label={t("cs.member")} value={answers.cips_member} onChange={set("cips_member")} />
        <YesNo label={t("cs.transcripts")} value={answers.transcripts_sent} onChange={set("transcripts_sent")} />
        <YesNo label={t("cs.references")} value={answers.references_ready} onChange={set("references_ready")} />
        <YesNo label={t("cs.skills")} value={answers.skills_assessment_done} onChange={set("skills_assessment_done")} />
      </section>
      <SubmitButton busy={report.busy} />
    </form>
    <ResultStatus busy={report.busy} ready={!!report.result} />
    {report.error && <p role="alert" className="rounded bg-rose-50 p-3 text-rose-900">{report.error}</p>}
    {report.result && <RoadmapView roadmap={report.result} />}
  </div>;
}
