"use client";

import { useId } from "react";
import { useI18n } from "@/lib/i18n";

type Tri = boolean | null;

export function YesNo({ label, hint, value, onChange }: {
  label: string; hint?: string; value: Tri; onChange: (v: Tri) => void;
}) {
  const name = useId();
  const { t } = useI18n();
  const options: [string, Tri][] = [[t("q.yes"), true], [t("q.no"), false], [t("q.notSure"), null]];
  return (
    <fieldset className="py-3">
      <legend className="font-medium">{label}</legend>
      {hint && <p className="text-sm text-slate-600">{hint}</p>}
      <div className="mt-2 flex flex-wrap gap-2">
        {options.map(([text, v]) => (
          <label key={text}
            className={`cursor-pointer rounded border px-3 py-1.5 text-sm has-[:focus-visible]:outline has-[:focus-visible]:outline-3 has-[:focus-visible]:outline-brand ${
              value === v ? "border-brand bg-brand text-white" : "border-slate-300 bg-white"}`}>
            <input type="radio" name={name} className="sr-only" checked={value === v} onChange={() => onChange(v)} />
            {text}
          </label>
        ))}
      </div>
    </fieldset>
  );
}

export function NumberQuestion({ label, hint, value, onChange, unit, max, step = 1 }: {
  label: string; hint?: string; value: number | null; onChange: (v: number | null) => void; unit?: string; max?: number;
  step?: number;
}) {
  const id = useId();
  return (
    <div className="py-3">
      <label htmlFor={id} className="font-medium">{label}</label>
      {hint && <p className="text-sm text-slate-600">{hint}</p>}
      <div className="mt-2 flex items-center gap-2">
        <input id={id} type="number" min={0} max={max} step={step} inputMode={step < 1 ? "decimal" : "numeric"}
          className="w-32 rounded border border-slate-300 px-2 py-1.5"
          value={value ?? ""} onChange={(e) => onChange(e.target.value === "" ? null : Number(e.target.value))} />
        {unit && <span className="text-sm text-slate-600">{unit}</span>}
      </div>
    </div>
  );
}

export function Choice<T extends string>({ label, hint, value, options, onChange, emptyLabel }: {
  label: string; hint?: string; value: T | null; options: [T, string][]; onChange: (v: T | null) => void; emptyLabel?: string;
}) {
  const id = useId();
  const { t } = useI18n();
  return (
    <div className="py-3">
      <label htmlFor={id} className="font-medium">{label}</label>
      {hint && <p className="text-sm text-slate-600">{hint}</p>}
      <select id={id} className="mt-2 block w-full max-w-full rounded border border-slate-300 bg-white px-2 py-1.5 sm:w-auto"
        value={value ?? ""} onChange={(e) => onChange((e.target.value || null) as T | null)}>
        <option value="">{emptyLabel ?? t("q.notSure")}</option>
        {options.map(([v, text]) => <option key={v} value={v}>{text}</option>)}
      </select>
    </div>
  );
}

/** Drops unanswered questions so the API treats them as unknown. */
export function answered<T extends object>(answers: T): Partial<T> {
  return Object.fromEntries(Object.entries(answers).filter(([, v]) => v !== null && v !== undefined)) as Partial<T>;
}
