export type Status = "done" | "to_do" | "to_confirm" | "may_apply" | "not_needed";

export interface RoadmapItem {
  id: string;
  title: string;
  category: string;
  description: string;
  status: Status;
  detail: string;
  source_url: string;
}

export interface Cost {
  name: string;
  amount: number;
  currency: "CAD" | "USD";
  gst: "included" | "excluded" | "not_applicable";
  payee: string;
  status: "to_do" | "may_apply";
  note: string;
  source_url: string;
}

export interface Roadmap {
  disclaimer: string;
  regulator: { id: string; name: string; short_name: string; designation: string; verified_on: string };
  pathway: { id: string; name: string; summary: string } | null;
  pathway_note: string | null;
  progress: Record<Status, number>;
  requirements: RoadmapItem[];
  next_steps: string[];
  costs: Cost[];
  cost_totals: { expected?: Record<string, number>; possible?: Record<string, number> };
  cost_notes: string[];
  timelines: { name: string; max_days: number | null; business_days: boolean; description: string | null; source_url: string }[];
}

export interface ExamMatch {
  exam: { code: string; title: string };
  score: number;
  status: "likely_covered" | "partial" | "possible_gap";
  best_course: { code: string; title: string } | null;
  shared_terms: string[];
}

export interface GapAnalysis {
  disclaimer: string;
  discipline: string;
  syllabus_source: string | null;
  courses_found: { code: string; title: string; credits: number | null; grade: string | null; description: string }[];
  groups: { name: string; kind: string; required: number; likely_covered: number; possibly_needed: number; exams: ExamMatch[] }[];
  document: { method: "text_layer" | "ocr"; pages: number; ocr_confidence: number | null } | null;
  notes: string[];
  summary: { courses_found: number; exams_required: number; likely_covered: number; possibly_needed: number };
}

export interface Discipline {
  id: string;
  name: string;
  edition: string | null;
}
