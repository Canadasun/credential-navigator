import type { Discipline, GapAnalysis, Roadmap } from "./types";

async function parse<T>(response: Response): Promise<T> {
  if (response.ok) return response.json() as Promise<T>;
  let message = `The service returned an error (${response.status}).`;
  try {
    const body = await response.json();
    if (typeof body.detail === "string") message = body.detail;
    else if (Array.isArray(body.detail)) {
      message = body.detail.map((item: { msg?: string }) => item.msg || "Check your answers.").join(" ");
    }
  } catch {
    /* keep the generic message */
  }
  throw new Error(message);
}

export async function fetchRoadmap(regulator: "apega" | "crna" | "acp" | "cips", answers: object, signal?: AbortSignal): Promise<Roadmap> {
  const response = await fetch(`/api/roadmap/${regulator}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(answers),
    signal,
  });
  return parse<Roadmap>(response);
}

export async function fetchDisciplines(): Promise<Discipline[]> {
  return parse<Discipline[]>(await fetch("/api/apega/disciplines"));
}

export async function analyseDocument(discipline: string, file: File, signal?: AbortSignal): Promise<GapAnalysis> {
  const form = new FormData();
  form.append("discipline", discipline);
  form.append("file", file);
  return parse<GapAnalysis>(await fetch("/api/apega/analysis", { method: "POST", body: form, signal }));
}

export function money(amount: number, currency: string, lang: "en" | "fr" = "en"): string {
  return new Intl.NumberFormat(lang === "fr" ? "fr-CA" : "en-CA", { style: "currency", currency, currencyDisplay: "code" })
    .format(amount);
}
