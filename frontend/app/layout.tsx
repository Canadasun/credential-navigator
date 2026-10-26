import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Credential Navigator",
  description: "Prepare for professional licensing in Alberta: your route, requirements, costs and gaps.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen">
        <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:p-2 focus:bg-white">
          Skip to content
        </a>
        <header>
          <nav className="bg-brand text-white" aria-label="Main">
            <div className="mx-auto flex max-w-5xl flex-wrap items-center gap-x-6 gap-y-2 px-4 py-3">
              <Link href="/" className="text-lg font-semibold">Credential Navigator</Link>
              <Link href="/engineering" className="hover:underline">Engineering (APEGA)</Link>
              <Link href="/nursing" className="hover:underline">Nursing (CRNA)</Link>
            </div>
          </nav>
          <div role="note" className="border-b border-amber-300 bg-amber-50">
            <p className="mx-auto max-w-5xl px-4 py-2 text-sm text-amber-900">
              <strong>Advisory tool.</strong> This site helps you prepare. It is not part of APEGA or the CRNA,
              and only the regulator decides on your registration.
            </p>
          </div>
        </header>
        <main id="main" className="mx-auto max-w-5xl px-4 py-8">{children}</main>
        <footer className="mx-auto max-w-5xl px-4 pb-10 text-xs text-slate-600">
          Requirements and fees come from the regulators&apos; public websites; each item links to its source.
          Your answers and documents are not stored.
        </footer>
      </body>
    </html>
  );
}
