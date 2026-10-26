"use client";

import { EnglishTest, englishPayload, type TestScale } from "@/components/EnglishTest";
import { DraftControls, ResultStatus, SectionNav, SubmitButton } from "@/components/PlanTools";
import { NumberQuestion, YesNo, answered } from "@/components/Questions";
import RoadmapView from "@/components/RoadmapView";
import { fetchRoadmap } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { useReport } from "@/lib/useReport";
import { isRecord, useDraft } from "@/lib/useDraft";
import type { Roadmap } from "@/lib/types";

type Test = "IELTS Academic" | "OET";
const PARTS = ["listening", "reading", "writing", "speaking"] as const;
// NAPRA's policy ignores the IELTS overall score, so only the four skills are asked for.
const SCALES: Record<Test, TestScale> = {
  "IELTS Academic": { parts: PARTS, step: 0.5, max: 9 },
  OET: { parts: PARTS, grades: ["A", "B", "C+", "C", "D", "E"] },
};

const emptyAnswers = {
  us_acpe_pharmd: null as boolean | null,
  gateway_enrolled: null as boolean | null,
  document_evaluation_done: null as boolean | null,
  pebc_part1_passed: null as boolean | null,
  pebc_part2_passed: null as boolean | null,
  pebc_both_first_attempt: null as boolean | null,
  dcpp_completed: null as boolean | null,
  english_exemption: null as boolean | null,
  criminal_record_check_done: null as boolean | null,
  provisional_registered: null as boolean | null,
  jurisprudence_done: null as boolean | null,
  spt_experiences_completed: null as number | null,
  liability_insurance: null as boolean | null,
};
const emptyDraft = { answers: emptyAnswers, test: null as Test | null, takenOn: "", scores: {} as Record<string, string> };
function validDraft(v: unknown) {
  if (!isRecord(v) || !isRecord(v.answers) || !isRecord(v.scores) || typeof v.takenOn !== "string" ||
      !(v.test === null || v.test === "IELTS Academic" || v.test === "OET")) return false;
  const answers = v.answers;
  if (Object.keys(answers).length !== Object.keys(emptyAnswers).length) return false;
  return Object.keys(emptyAnswers).every(k => {
    const value = answers[k];
    if (k === "spt_experiences_completed") return value === null || typeof value === "number" && Number.isInteger(value) && value >= 0 && value <= 10;
    return value === null || typeof value === "boolean";
  }) && Object.entries(v.scores).every(([k, value]) => (PARTS as readonly string[]).includes(k) && typeof value === "string");
}

export default function Pharmacy() {
  const { t } = useI18n();
  const draft = useDraft("navigator-pharmacy-v1", emptyDraft, validDraft);
  const { answers: a, test, takenOn, scores } = draft.value;
  const report = useReport<Roadmap>();
  function update(change: Partial<typeof emptyDraft>) { report.invalidate(); draft.setValue(s => ({ ...s, ...change })); }
  const set = <K extends keyof typeof a>(key: K) => (value: (typeof a)[K]) => {
    report.invalidate();
    draft.setValue(s => {
      const answers = { ...s.answers, [key]: value };
      // "Both parts on the first attempt" only makes sense once both parts are passed.
      if (!(answers.pebc_part1_passed && answers.pebc_part2_passed)) answers.pebc_both_first_attempt = null;
      return { ...s, answers };
    });
  };
  function setTest(value: Test | null) {
    report.invalidate();
    draft.setValue(s => ({ ...s, test: value, takenOn: "", scores: {}, answers: { ...s.answers, english_exemption: null } }));
  }
  async function submit(event: React.FormEvent) {
    event.preventDefault();
    const english = englishPayload(SCALES, test, takenOn, scores);
    const { english_exemption, ...rest } = a;
    const payload = { ...answered(rest), ...(english ? { english } : answered({ english_exemption })) };
    await report.run(signal => fetchRoadmap("acp", payload, signal));
  }
  const bothPassed = a.pebc_part1_passed === true && a.pebc_part2_passed === true;

  return (
    <div className="space-y-7">
      <div><p className="mb-2 text-sm font-semibold uppercase tracking-wider text-brand">{t("rx.kicker")}</p>
        <h1 className="text-3xl font-bold">{t("rx.title")}</h1>
        <p className="mt-2 max-w-2xl text-slate-700">{t("rx.lead")} {t("form.intro")}</p></div>
      <SectionNav sections={[["education", t("rx.navEducation")], ["exams", t("rx.navExams")], ["english", t("rx.navEnglish")],
        ["registers", t("rx.navRegister")], ...(report.result ? [["roadmap-title", t("form.roadmap")], ["costs", t("form.costs")]] as [string, string][] : [])]} />
      <DraftControls enabled={draft.enabled} toggle={draft.toggle} notice={draft.notice} />
      <form onSubmit={submit} className="rounded-xl border border-slate-200 bg-white px-5">
        <section id="education" className="form-section" aria-labelledby="education-heading"><h2 id="education-heading">{t("rx.s1")}</h2>
          <YesNo label={t("rx.usPharmd")} hint={t("rx.usPharmdHint")} value={a.us_acpe_pharmd} onChange={set("us_acpe_pharmd")} />
          <YesNo label={t("rx.gateway")} value={a.gateway_enrolled} onChange={set("gateway_enrolled")} />
          <YesNo label={t("rx.documentEvaluation")} value={a.document_evaluation_done} onChange={set("document_evaluation_done")} />
        </section>
        <section id="exams" className="form-section" aria-labelledby="exams-heading"><h2 id="exams-heading">{t("rx.s2")}</h2>
          <YesNo label={t("rx.part1")} value={a.pebc_part1_passed} onChange={set("pebc_part1_passed")} />
          <YesNo label={t("rx.part2")} value={a.pebc_part2_passed} onChange={set("pebc_part2_passed")} />
          {bothPassed && <YesNo label={t("rx.firstAttempt")} hint={t("rx.firstAttemptHint")}
            value={a.pebc_both_first_attempt} onChange={set("pebc_both_first_attempt")} />}
          {a.us_acpe_pharmd !== true && <YesNo label={t("rx.dcpp")} hint={t("rx.dcppHint")}
            value={a.dcpp_completed} onChange={set("dcpp_completed")} />}
        </section>
        <section id="english" className="form-section" aria-labelledby="english-heading"><h2 id="english-heading">{t("rx.s3")}</h2>
          <EnglishTest legend={t("rx.englishLegend")} hint={test === "OET" ? `${t("rx.englishHint")} ${t("rx.oetHint")}` : t("rx.englishHint")}
            scales={SCALES} test={test} takenOn={takenOn} scores={scores} onTest={setTest} onDate={(d) => update({ takenOn: d })}
            onScore={(part, value) => update({ scores: { ...scores, [part]: value } })} />
          {!test && <YesNo label={t("rx.exemption")} hint={t("rx.exemptionHint")} value={a.english_exemption} onChange={set("english_exemption")} />}
        </section>
        <section id="registers" className="form-section" aria-labelledby="registers-heading"><h2 id="registers-heading">{t("rx.s4")}</h2>
          <YesNo label={t("rx.criminal")} value={a.criminal_record_check_done} onChange={set("criminal_record_check_done")} />
          <YesNo label={t("rx.provisional")} value={a.provisional_registered} onChange={set("provisional_registered")} />
          <YesNo label={t("rx.jurisprudence")} value={a.jurisprudence_done} onChange={set("jurisprudence_done")} />
          <NumberQuestion label={t("rx.spt")} hint={t("rx.sptHint")} unit={t("unit.experiences")} max={10}
            value={a.spt_experiences_completed} onChange={set("spt_experiences_completed")} />
          <YesNo label={t("rx.liability")} value={a.liability_insurance} onChange={set("liability_insurance")} />
        </section>
        <SubmitButton busy={report.busy} />
      </form>
      <ResultStatus busy={report.busy} ready={!!report.result} />
      {report.error && <p role="alert" className="rounded bg-rose-50 p-3 text-rose-900">{report.error}</p>}
      {report.result && <RoadmapView roadmap={report.result} />}
    </div>
  );
}
