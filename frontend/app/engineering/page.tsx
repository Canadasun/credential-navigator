"use client";

import DocumentUploader from "@/components/DocumentUploader";
import { NumberQuestion, YesNo, answered } from "@/components/Questions";
import RoadmapView from "@/components/RoadmapView";
import { DraftControls, ResultStatus, SectionNav, SubmitButton } from "@/components/PlanTools";
import { fetchRoadmap } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
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
  const { t } = useI18n();
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
    <div><p className="mb-2 text-sm font-semibold uppercase tracking-wider text-brand">{t("eng.kicker")}</p>
      <h1 className="text-3xl font-bold">{t("eng.title")}</h1>
      <p className="mt-2 max-w-2xl text-slate-700">{t("form.intro")}</p></div>
    <SectionNav sections={[["profile", t("eng.navProfile")], ["readiness", t("eng.navReadiness")],
      ...(report.result ? [["roadmap-title", t("form.roadmap")], ["costs", t("form.costs")]] as [string, string][] : []),
      ["gap-title", t("eng.navCourses")]]} />
    <DraftControls enabled={draft.enabled} toggle={draft.toggle} notice={draft.notice} />
    <form onSubmit={submit} className="rounded-xl border border-slate-200 bg-white px-5">
      <section id="profile" className="form-section" aria-labelledby="profile-heading"><h2 id="profile-heading">{t("eng.s1")}</h2>
        <NumberQuestion label={t("eng.experience")} unit={t("unit.months")} max={720}
          hint={t("eng.experienceHint")} value={answers.experience_months} onChange={set("experience_months")} />
        <YesNo label={t("eng.pr")} value={answers.canadian_citizen_or_pr} onChange={set("canadian_citizen_or_pr")} />
        <YesNo label={t("eng.ceab")} hint={t("eng.ceabHint")}
          value={answers.ceab_accredited_degree} onChange={set("ceab_accredited_degree")} />
      </section>
      <section id="readiness" className="form-section" aria-labelledby="readiness-heading"><h2 id="readiness-heading">{t("eng.s2")}</h2>
        <YesNo label={t("eng.wes")} value={answers.wes_icap_received} onChange={set("wes_icap_received")} />
        <YesNo label={t("eng.nppe")} value={answers.nppe_passed} onChange={set("nppe_passed")} />
        <YesNo label={t("eng.english")} value={answers.english_competent} onChange={set("english_competent")} />
        <YesNo label={t("eng.references")} value={answers.references_ready} onChange={set("references_ready")} />
      </section>
      <SubmitButton busy={report.busy} />
    </form>
    <ResultStatus busy={report.busy} ready={!!report.result} />
    {report.error && <p role="alert" className="rounded bg-rose-50 p-3 text-rose-900">{report.error}</p>}
    {report.result && <RoadmapView roadmap={report.result} />}
    <DocumentUploader />
  </div>;
}
