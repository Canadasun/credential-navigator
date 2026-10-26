import Link from "next/link";

const professions = [
  {
    href: "/engineering",
    title: "Engineering",
    regulator: "APEGA, P.Eng. or Licensee",
    text: "Your route, requirements, fees and timelines, plus a comparison of your courses with APEGA's exam syllabus.",
  },
  {
    href: "/nursing",
    title: "Registered nursing",
    regulator: "CRNA, Registered Nurse",
    text: "Check practice hours, English scores, the NCLEX-RN and every other requirement, with costs and next steps.",
  },
];

export default function Home() {
  return (
    <div className="space-y-8">
      <section className="rounded-2xl border border-slate-200 bg-white px-6 py-8 sm:p-10">
        <p className="mb-3 text-sm font-semibold uppercase tracking-wider text-brand">For internationally trained professionals</p>
        <h1 className="max-w-2xl text-3xl font-bold sm:text-4xl">Your path to licensing in Alberta</h1>
        <p className="mt-3 max-w-2xl text-lg text-slate-700">
          Trained outside Canada? Answer a few questions to see what you have already done, what is left, what it
          will cost and how long it takes.
        </p>
      </section>
      <ol aria-label="How it works" className="grid gap-4 text-sm sm:grid-cols-3">
        {[["01", "Choose your profession", "Start with engineering or registered nursing."], ["02", "Answer what you know", "Unsure answers become questions to follow up."], ["03", "Review your next steps", "See requirements, costs and linked sources."]].map(([n, title, text]) =>
          <li key={n} className="rounded-xl border border-slate-200 bg-white p-5"><span className="text-xs font-bold text-brand">{n}</span><h2 className="mt-2 font-semibold">{title}</h2><p className="mt-1 text-slate-600">{text}</p></li>)}
      </ol>
      <h2 className="text-xl font-semibold">Choose your profession</h2>
      <div className="grid gap-4 sm:grid-cols-2">
        {professions.map((p) => (
          <Link key={p.href} href={p.href}
            className="block rounded-lg border border-slate-200 bg-white p-6 shadow-sm transition hover:border-brand hover:shadow">
            <h2 className="text-xl font-semibold text-brand">{p.title}</h2>
            <p className="text-sm font-medium text-slate-600">{p.regulator}</p>
            <p className="mt-3 text-slate-700">{p.text}</p>
            <span className="mt-4 inline-block font-medium text-brand">Start {p.title.toLowerCase()} →</span>
          </Link>
        ))}
      </div>
    </div>
  );
}
