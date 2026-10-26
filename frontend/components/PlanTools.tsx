"use client";
import { useEffect } from "react";
import { useI18n, type MessageKey } from "@/lib/i18n";

export function SectionNav({ sections }: { sections: [string, string][] }) {
  const { t } = useI18n();
  return <nav aria-label={t("form.onThisPage")} className="section-nav no-print">
    <span className="text-xs font-bold uppercase tracking-wider text-slate-600">{t("form.onThisPage")}</span>
    {sections.map(([id, title]) => <a key={id} href={`#${id}`} className="rounded-md px-3 py-2 text-sm font-medium text-brand hover:bg-sky-50">{title}</a>)}
  </nav>;
}

export function DraftControls({ enabled, toggle, notice }: { enabled: boolean; toggle: (next: boolean) => void; notice: MessageKey | null }) {
  const { t } = useI18n();
  return <aside className="draft-controls no-print" aria-label={t("draft.region")}>
    <label className="flex items-start gap-2 font-medium"><input type="checkbox" checked={enabled} onChange={e => toggle(e.target.checked)} className="mt-1" />{t("draft.save")}</label>
    <p className="mt-1 text-sm text-slate-600">{t("draft.help")}</p>
    {enabled && <button type="button" onClick={() => toggle(false)} className="mt-2 text-sm font-medium text-brand underline">{t("draft.delete")}</button>}
    <p role="status" className="mt-1 text-sm text-slate-600">{notice ? t(notice) : ""}</p>
  </aside>;
}

export function ResultStatus({ busy, ready, id = "roadmap-title", label }: { busy: boolean; ready: boolean; id?: string; label?: string }) {
  const { t } = useI18n();
  const name = label ?? t("roadmap.title");
  useEffect(() => {
    if (ready) {
      const heading = document.getElementById(id);
      heading?.focus({ preventScroll: true });
      heading?.scrollIntoView({ block: "start", behavior: "instant" });
    }
  }, [ready, id]);
  return <p role="status" aria-live="polite" className="text-sm text-brand">{busy ? t("status.preparing", { label: name }) : ready ? t("status.ready", { label: name }) : ""}</p>;
}

export function ExportTools({ value, filename }: { value: unknown; filename: string }) {
  const { t } = useI18n();
  function download() {
    const url = URL.createObjectURL(new Blob([JSON.stringify(value, null, 2)], { type: "application/json" }));
    const a = document.createElement("a"); a.href = url; a.download = filename; a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  return <div className="no-print flex flex-wrap gap-3">
    <button type="button" onClick={() => window.print()} className="secondary-button">{t("export.print")}</button>
    <button type="button" onClick={download} className="secondary-button">{t("export.json")}</button>
  </div>;
}

export function SubmitButton({ busy }: { busy: boolean }) {
  const { t } = useI18n();
  return <div className="py-5">
    <button type="submit" disabled={busy} className="rounded-lg bg-brand px-5 py-3 font-semibold text-white hover:bg-brand-dark disabled:opacity-60">
      {busy ? t("form.submitting") : t("form.submit")}</button>
    <p className="mt-2 text-sm text-slate-600">{t("form.editClears")}</p>
  </div>;
}
