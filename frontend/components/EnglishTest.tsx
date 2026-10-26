"use client";

import { Choice } from "./Questions";
import { useI18n } from "@/lib/i18n";

export type Part = "listening" | "reading" | "writing" | "speaking" | "overall";
/** How each accepted test is scored: bands with a step and maximum, or letter grades. */
export type TestScale = { parts: readonly Part[]; step: number; max: number } | { parts: readonly Part[]; grades: readonly string[] };

export function EnglishTest<T extends string>({ legend, hint, scales, test, takenOn, scores, onTest, onDate, onScore }: {
  legend: string; hint: string; scales: Record<T, TestScale>; test: T | null; takenOn: string;
  scores: Record<string, string>; onTest: (test: T | null) => void; onDate: (date: string) => void;
  onScore: (part: Part, value: string) => void;
}) {
  const { t } = useI18n();
  const scale = test ? scales[test] : null;
  return (
    <fieldset className="py-3">
      <legend className="font-medium">{legend}</legend>
      <p className="text-sm text-slate-600">{hint}</p>
      <div className="mt-2 flex flex-wrap gap-3">
        <Choice label={t("english.test")} emptyLabel={t("english.noTest")} value={test}
          options={(Object.keys(scales) as T[]).map((name) => [name, name] as [T, string])} onChange={onTest} />
        {test && (
          <div className="py-3">
            <label htmlFor="taken" className="font-medium">{t("english.dateTaken")}</label>
            <input id="taken" type="date" required max={new Date().toLocaleDateString("en-CA")} aria-describedby="date-help"
              value={takenOn} onChange={(e) => onDate(e.target.value)} className="mt-2 block rounded border border-slate-300 px-2 py-1.5" />
            <p id="date-help" className="mt-1 text-sm text-slate-600">{t("english.dateHelp")}</p>
          </div>
        )}
      </div>
      {test && <p className="mb-2 text-sm text-slate-600">{t("english.using", { test })}</p>}
      {scale && (
        <div className="flex flex-wrap gap-3">
          {scale.parts.map((part) => (
            <div key={part}>
              <label htmlFor={`score-${part}`} className="block text-sm capitalize">{t(`part.${part}`)}</label>
              {"grades" in scale ? (
                <select id={`score-${part}`} value={scores[part] ?? ""} onChange={(e) => onScore(part, e.target.value)}
                  className="w-28 rounded border border-slate-300 bg-white px-2 py-1">
                  <option value="">{t("english.notTaken")}</option>
                  {scale.grades.map((g) => <option key={g} value={g}>{g}</option>)}
                </select>
              ) : (
                <input id={`score-${part}`} type="number" step={scale.step} min={0} max={scale.max} value={scores[part] ?? ""}
                  onChange={(e) => onScore(part, e.target.value)} className="w-20 rounded border border-slate-300 px-2 py-1" />
              )}
            </div>
          ))}
        </div>
      )}
    </fieldset>
  );
}

/** The scores to send: numbers for band scales, letters for graded tests; blank parts stay missing. */
export function englishPayload<T extends string>(scales: Record<T, TestScale>, test: T | null, takenOn: string,
                                                 scores: Record<string, string>) {
  if (!test || !takenOn) return null;
  const scale = scales[test];
  const entered = scale.parts.filter((p) => scores[p] !== undefined && scores[p] !== "");
  return { test, taken_on: takenOn,
    scores: Object.fromEntries(entered.map((p) => [p, "grades" in scale ? scores[p] : Number(scores[p])])) };
}
