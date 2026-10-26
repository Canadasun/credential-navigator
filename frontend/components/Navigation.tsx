"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
export default function Navigation() {
  const current = usePathname();
  return <nav className="bg-brand text-white" aria-label="Main">
    <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-4 py-4">
      <Link href="/" className="text-lg font-bold tracking-tight" aria-current={current === "/" ? "page" : undefined}>Credential Navigator</Link>
      <div className="flex flex-wrap gap-2 text-sm font-medium">
        {[["/engineering", "Engineering (APEGA)"], ["/nursing", "Nursing (CRNA)"]].map(([href, label]) =>
          <Link key={href} href={href} aria-current={current === href ? "page" : undefined}
            className={`rounded-lg px-3 py-2 ${current === href ? "bg-white text-brand" : "hover:bg-white/15"}`}>{label}</Link>)}
      </div>
    </div>
  </nav>;
}
