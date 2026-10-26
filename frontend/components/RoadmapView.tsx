import { money } from "@/lib/api";
import type { Roadmap, Status } from "@/lib/types";

const LABELS: Record<Status, { text: string; style: string }> = {
  done: { text: "Done", style: "bg-emerald-100 text-emerald-900" },
  to_do: { text: "To do", style: "bg-sky-100 text-sky-900" },
  to_confirm: { text: "To confirm", style: "bg-amber-100 text-amber-900" },
  may_apply: { text: "May apply", style: "bg-violet-100 text-violet-900" },
  not_needed: { text: "Not needed", style: "bg-slate-100 text-slate-600" },
};

function totals(values?: Record<string, number>) {
  if (!values) return "None";
  return Object.entries(values).map(([currency, amount]) => money(amount, currency)).join(" + ");
}

export default function RoadmapView({ roadmap }: { roadmap: Roadmap }) {
  const counted = roadmap.requirements.filter((r) => r.status !== "not_needed" && r.status !== "may_apply");
  const done = counted.filter((r) => r.status === "done").length;
  return (
    <section aria-labelledby="roadmap-title" className="space-y-6">
      <div className="rounded-lg border border-slate-200 bg-white p-5">
        <h2 id="roadmap-title" className="text-2xl font-semibold">Your roadmap</h2>
        {roadmap.pathway ? (
          <p className="mt-2"><span className="font-medium">Route: {roadmap.pathway.name}.</span> {roadmap.pathway.summary}</p>
        ) : (
          <p className="mt-2 text-amber-900">{roadmap.pathway_note}</p>
        )}
        <div className="mt-4">
          <div className="flex justify-between text-sm"><span>{done} of {counted.length} requirements done</span></div>
          <div className="mt-1 h-3 rounded bg-slate-200" role="progressbar" aria-valuemin={0}
            aria-valuemax={counted.length} aria-valuenow={done} aria-label="Requirements done">
            <div className="h-3 rounded bg-emerald-600" style={{ width: `${counted.length ? (100 * done) / counted.length : 0}%` }} />
          </div>
        </div>
      </div>

      {roadmap.next_steps.length > 0 && (
        <div className="rounded-lg border border-slate-200 bg-white p-5">
          <h3 className="text-lg font-semibold">Next steps</h3>
          <ol className="mt-2 list-decimal space-y-1 pl-5">
            {roadmap.next_steps.map((step) => <li key={step}>{step}</li>)}
          </ol>
        </div>
      )}

      <div className="rounded-lg border border-slate-200 bg-white p-5">
        <h3 className="text-lg font-semibold">Requirements</h3>
        <ul className="mt-2 divide-y divide-slate-100">
          {roadmap.requirements.map((r) => (
            <li key={r.id} className="py-3">
              <div className="flex flex-wrap items-center gap-2">
                <span className={`rounded px-2 py-0.5 text-xs font-semibold ${LABELS[r.status].style}`}>{LABELS[r.status].text}</span>
                <span className="font-medium">{r.title}</span>
              </div>
              {r.detail && <p className="mt-1 text-sm">{r.detail}</p>}
              <p className="mt-1 text-sm text-slate-600">
                {r.description}{" "}
                <a href={r.source_url} target="_blank" rel="noreferrer" className="text-brand underline">Source</a>
              </p>
            </li>
          ))}
        </ul>
      </div>

      <div className="rounded-lg border border-slate-200 bg-white p-5">
        <h3 className="text-lg font-semibold">Costs</h3>
        <p className="mt-1">Expected: <strong>{totals(roadmap.cost_totals.expected)}</strong></p>
        <p className="text-sm text-slate-600">Possible, if the regulator asks: {totals(roadmap.cost_totals.possible)}</p>
        <div className="mt-3 overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead><tr className="border-b text-slate-600"><th className="py-1 pr-3">Fee</th><th className="pr-3">Paid to</th><th className="pr-3">Amount</th><th>When</th></tr></thead>
            <tbody>
              {roadmap.costs.map((c) => (
                <tr key={c.name} className="border-b border-slate-100 align-top">
                  <td className="py-2 pr-3"><a href={c.source_url} target="_blank" rel="noreferrer" className="underline">{c.name}</a></td>
                  <td className="pr-3">{c.payee}</td>
                  <td className="pr-3 whitespace-nowrap">{money(c.amount, c.currency)}{c.gst === "excluded" ? " + GST" : ""}</td>
                  <td>{c.status === "may_apply" ? "Only if needed. " : ""}{c.note}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <ul className="mt-3 list-disc pl-5 text-sm text-slate-600">
          {roadmap.cost_notes.map((n) => <li key={n}>{n}</li>)}
        </ul>
      </div>

      <div className="rounded-lg border border-slate-200 bg-white p-5">
        <h3 className="text-lg font-semibold">Timelines</h3>
        <ul className="mt-2 space-y-1 text-sm">
          {roadmap.timelines.map((t) => (
            <li key={t.name}>
              <span className="font-medium">{t.name}</span>
              {t.max_days && `: up to ${t.max_days} ${t.business_days ? "business " : ""}days`}
              {t.description && `. ${t.description}`}
            </li>
          ))}
        </ul>
      </div>
      <p className="text-sm text-slate-600">{roadmap.disclaimer}</p>
    </section>
  );
}
