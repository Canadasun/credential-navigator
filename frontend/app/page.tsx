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
      <section>
        <h1 className="text-3xl font-bold">Your path to licensing in Alberta</h1>
        <p className="mt-3 max-w-2xl text-lg text-slate-700">
          Trained outside Canada? Answer a few questions to see what you have already done, what is left, what it
          will cost and how long it takes.
        </p>
      </section>
      <div className="grid gap-4 sm:grid-cols-2">
        {professions.map((p) => (
          <Link key={p.href} href={p.href}
            className="block rounded-lg border border-slate-200 bg-white p-6 shadow-sm transition hover:border-brand hover:shadow">
            <h2 className="text-xl font-semibold text-brand">{p.title}</h2>
            <p className="text-sm font-medium text-slate-600">{p.regulator}</p>
            <p className="mt-3 text-slate-700">{p.text}</p>
            <span className="mt-4 inline-block font-medium text-brand">Start →</span>
          </Link>
        ))}
      </div>
    </div>
  );
}
