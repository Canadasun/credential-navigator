"use client";

import { EnglishTest, englishPayload, type TestScale } from "@/components/EnglishTest";
import { DraftControls, ResultStatus, SectionNav, SubmitButton } from "@/components/PlanTools";
import { Choice, NumberQuestion, YesNo, answered } from "@/components/Questions";
import RoadmapView from "@/components/RoadmapView";
import { fetchRoadmap } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { useReport } from "@/lib/useReport";
import { isRecord, useDraft } from "@/lib/useDraft";
import type { Roadmap } from "@/lib/types";

type Report = "nnas" | "eca" | "none";
type Rating = "comparable" | "somewhat comparable" | "not comparable";
type Test = "IELTS Academic" | "CELBAN";
const SCALES: Record<Test, TestScale> = {
  "IELTS Academic": { parts: ["listening", "reading", "writing", "speaking", "overall"], step: 0.5, max: 9 },
  CELBAN: { parts: ["listening", "reading", "writing", "speaking"], step: 1, max: 12 },
};

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
  }) && Object.entries(v.scores).every(([k, value]) => (SCALES["IELTS Academic"].parts as readonly string[]).includes(k) && typeof value === "string");
}

export default function Nursing() {
  const { t } = useI18n();
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
    const english = englishPayload(SCALES, test, takenOn, scores);
    const { english_exemption, nnas_rating, ...rest } = a;
    const payload = { ...answered(rest), ...(a.credential_report === "nnas" ? { nnas_rating } : {}),
      ...(english ? { english } : { english_exemption }) };
    await report.run(signal => fetchRoadmap("crna", payload, signal));
  }

  return (
    <div className="space-y-7">
      <div>
        <h1 className="text-3xl font-bold">{t("rn.title")}</h1>
        <p className="mt-2 text-slate-700">{t("form.intro")}</p>
      </div>
      <SectionNav sections={[["education", t("rn.navEducation")], ["practice", t("rn.navPractice")], ["english", t("rn.navEnglish")],
        ["checks", t("rn.navChecks")], ...(report.result ? [["roadmap-title", t("form.roadmap")], ["costs", t("form.costs")]] as [string, string][] : [])]} />
      <DraftControls enabled={draft.enabled} toggle={draft.toggle} notice={draft.notice} />
      <form onSubmit={submit} className="rounded-xl border border-slate-200 bg-white px-5">
        <section id="education" className="form-section" aria-labelledby="education-heading"><h2 id="education-heading">{t("rn.s1")}</h2>
          <YesNo label={t("rn.nclex")} value={a.nclex_passed} onChange={set("nclex_passed")} />
          <Choice label={t("rn.report")} value={a.credential_report}
            options={[["nnas", t("rn.reportNnas")], ["eca", t("rn.reportEca")], ["none", t("rn.reportNone")]]}
            onChange={set("credential_report")} />
          {a.credential_report === "nnas" && (
            <Choice label={t("rn.rating")} value={a.nnas_rating}
              options={[["comparable", t("rn.comparable")], ["somewhat comparable", t("rn.somewhat")], ["not comparable", t("rn.notComparable")]]}
              onChange={set("nnas_rating")} />
          )}
        </section>
        <section id="practice" className="form-section" aria-labelledby="practice-heading"><h2 id="practice-heading">{t("rn.s2")}</h2>
          <NumberQuestion label={t("rn.hours2")} unit={t("unit.hours")} hint={t("rn.hours2Hint")}
            value={a.practice_hours_last_2_years} onChange={set("practice_hours_last_2_years")} />
          <NumberQuestion label={t("rn.hours5")} unit={t("unit.hours")}
            value={a.practice_hours_last_5_years} onChange={set("practice_hours_last_5_years")} />
          <YesNo label={t("rn.program")} value={a.qualifying_program_last_5_years} onChange={set("qualifying_program_last_5_years")} />
        </section>
        <section id="english" className="form-section" aria-labelledby="english-heading"><h2 id="english-heading">{t("rn.s3")}</h2>
          <EnglishTest legend={t("rn.englishLegend")} hint={t("rn.englishHint")} scales={SCALES} test={test} takenOn={takenOn}
            scores={scores} onTest={setTest} onDate={(d) => update({ takenOn: d })}
            onScore={(part, value) => update({ scores: { ...scores, [part]: value } })} />
          {!test && (
            <YesNo label={t("rn.exemption")} hint={t("rn.exemptionHint")} value={a.english_exemption} onChange={set("english_exemption")} />
          )}
        </section>
        <section id="checks" className="form-section" aria-labelledby="checks-heading"><h2 id="checks-heading">{t("rn.s4")}</h2>
          <YesNo label={t("rn.criminal")} value={a.criminal_record_check_done} onChange={set("criminal_record_check_done")} />
          <YesNo label={t("rn.jurisprudence")} value={a.jurisprudence_done} onChange={set("jurisprudence_done")} />
          <YesNo label={t("rn.sexualAbuse")} value={a.sexual_abuse_course_done} onChange={set("sexual_abuse_course_done")} />
          <YesNo label={t("rn.liability")} value={a.liability_protection} onChange={set("liability_protection")} />
        </section>
        <SubmitButton busy={report.busy} />
      </form>
      <ResultStatus busy={report.busy} ready={!!report.result} />
      {report.error && <p role="alert" className="rounded bg-rose-50 p-3 text-rose-900">{report.error}</p>}
      {report.result && <RoadmapView roadmap={report.result} />}
    </div>
  );
}
