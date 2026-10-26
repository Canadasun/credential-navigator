"use client";
import { useEffect } from "react";

export function SectionNav({ sections }: { sections: [string, string][] }) {
  return <nav aria-label="On this page" className="section-nav no-print">
    <span className="text-xs font-bold uppercase tracking-wider text-slate-500">On this page</span>
    {sections.map(([id, title]) => <a key={id} href={`#${id}`} className="rounded-md px-3 py-2 text-sm font-medium text-brand hover:bg-sky-50">{title}</a>)}
  </nav>;
}

export function DraftControls({ enabled, toggle, notice }: { enabled: boolean; toggle: (next: boolean) => void; notice: string }) {
  return <aside className="draft-controls no-print" aria-label="Draft settings">
    <label className="flex items-start gap-2 font-medium"><input type="checkbox" checked={enabled} onChange={e => toggle(e.target.checked)} className="mt-1" />Save my answers on this browser</label>
    <p className="mt-1 text-sm text-slate-600">Optional. Without saving, answers reset when you leave or reload. Uploaded files are never saved.</p>
    {enabled && <button type="button" onClick={() => toggle(false)} className="mt-2 text-sm font-medium text-brand underline">Delete saved draft</button>}
    <p role="status" className="mt-1 text-sm text-slate-600">{notice}</p>
  </aside>;
}

export function ResultStatus({ busy, ready, id = "roadmap-title", label = "Your roadmap" }: { busy: boolean; ready: boolean; id?: string; label?: string }) {
  useEffect(() => {
    if (ready) {
      const heading = document.getElementById(id);
      heading?.focus({ preventScroll: true });
      heading?.scrollIntoView({ block: "start", behavior: "instant" });
    }
  }, [ready, id]);
  return <p role="status" aria-live="polite" className="text-sm text-brand">{busy ? `${label} is being prepared…` : ready ? `${label} is ready. Results reflect your submitted answers.` : ""}</p>;
}

export function ExportTools({ value, filename }: { value: unknown; filename: string }) {
  function download() {
    const url = URL.createObjectURL(new Blob([JSON.stringify(value, null, 2)], { type: "application/json" }));
    const a = document.createElement("a"); a.href = url; a.download = filename; a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  return <div className="no-print flex flex-wrap gap-3">
    <button type="button" onClick={() => window.print()} className="secondary-button">Print / save PDF</button>
    <button type="button" onClick={download} className="secondary-button">Download report (JSON)</button>
  </div>;
}
