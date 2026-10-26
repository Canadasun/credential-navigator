"""Compare an applicant's courses with APEGA's exam syllabus for one discipline.

Similarity is TF-IDF cosine over words, with IDF learned from all exam descriptions, so
generic words ("engineering", "design") count for little and specific ones ("laplace",
"thermodynamics") for a lot. Every match reports the shared terms that produced it, so
an applicant or advisor can see why. This is a preparation aid: only APEGA's Board of
Examiners decides which exams an applicant must write.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass

LIKELY = 0.30   # similarity at or above which a course probably covers an exam
PARTIAL = 0.15  # between PARTIAL and LIKELY: some overlap, worth a closer look

STOPWORDS = set("""a an and are as at be by for from in into is it its of on or such that the their this to
use used using with including include includes introduction principles basic basics fundamentals topics
course study studies concepts concept methods method applications application analysis theory
engineering engineers engineer general i ii iii iv elementary advanced""".split())


def tokens(text: str) -> list[str]:
    words = re.findall(r"[a-z][a-z\-]+", text.lower())
    out = []
    for word in words:
        word = word.strip("-")
        if word in STOPWORDS or len(word) < 3:
            continue
        for suffix, repl in (("ies", "y"), ("sses", "ss"), ("s", "")):
            if word.endswith(suffix) and not word.endswith("ss") and len(word) > 3:
                word = word[: -len(suffix)] + repl
                break
        out.append(word)
    return out


@dataclass
class Exam:
    code: str
    title: str
    description: str
    priority: int = 0  # lower is assigned courses first (compulsory exams before electives)


class Vectoriser:
    def __init__(self, corpus: list[str]):
        documents = [set(tokens(text)) for text in corpus]
        frequency = Counter(word for doc in documents for word in doc)
        n = len(documents)
        self.idf = {word: math.log((1 + n) / (1 + df)) + 1 for word, df in frequency.items()}
        self.default_idf = math.log(1 + n) + 1

    def vector(self, text: str) -> dict[str, float]:
        counts = Counter(tokens(text))
        vec = {w: (1 + math.log(c)) * self.idf.get(w, self.default_idf) for w, c in counts.items()}
        norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
        return {w: v / norm for w, v in vec.items()}


def cosine(a: dict[str, float], b: dict[str, float]) -> tuple[float, list[str]]:
    shared = set(a) & set(b)
    score = sum(a[w] * b[w] for w in shared)
    top = sorted(shared, key=lambda w: a[w] * b[w], reverse=True)[:6]
    return score, top


def exam_text(exam: Exam) -> str:
    # The title is repeated so that a transcript line with only a course title can still match.
    return f"{exam.title} {exam.title} {exam.title} {exam.description}"


def course_text(course: dict) -> str:
    return f"{course['title']} {course['title']} {course.get('description') or ''}"


def status(score: float) -> str:
    return "likely_covered" if score >= LIKELY else "partial" if score >= PARTIAL else "possible_gap"


def match_exams(courses: list[dict], exams: list[Exam], corpus: list[Exam]) -> dict[str, dict]:
    """Assign courses to exams: {code: {score, status, best_course, shared_terms}}.

    Each course counts toward one exam only, as in an academic assessment. Exams are
    given in priority order (compulsory before elective); within each priority tier the
    strongest pairs are assigned first. An exam with no course left keeps score 0.
    """
    vectoriser = Vectoriser([exam_text(e) for e in corpus])
    course_vectors = [vectoriser.vector(course_text(c)) for c in courses]
    results, used = {}, set()
    for tier in _tiers(exams):
        pairs = []
        for exam in tier:
            exam_vector = vectoriser.vector(exam_text(exam))
            for index, vector in enumerate(course_vectors):
                score, shared = cosine(exam_vector, vector)
                if score > 0:
                    pairs.append((score, exam, index, shared))
        assigned = set()
        for score, exam, index, shared in sorted(pairs, key=lambda p: p[0], reverse=True):
            if exam.code in assigned or index in used:
                continue
            assigned.add(exam.code)
            used.add(index)
            results[exam.code] = _result(exam, score, courses[index], shared)
        for exam in tier:
            results.setdefault(exam.code, _result(exam, 0.0, None, []))
    return results


def _tiers(exams: list[Exam]) -> list[list[Exam]]:
    tiers: dict[int, list[Exam]] = {}
    for exam in exams:
        tiers.setdefault(getattr(exam, "priority", 0), []).append(exam)
    return [tiers[k] for k in sorted(tiers)]


def _result(exam: Exam, score: float, course: dict | None, shared: list[str]) -> dict:
    return {
        "exam": {"code": exam.code, "title": exam.title},
        "score": round(score, 3),
        "status": status(score),
        "best_course": {"code": course["code"], "title": course["title"]} if course else None,
        "shared_terms": shared,
    }


def evaluate_groups(groups: list[dict], matches: dict[str, dict]) -> list[dict]:
    """For each group: which exams look covered and how many more look needed.

    Compulsory groups need every exam; for elective or "choose N" groups, the N best-covered
    exams count.
    """
    report = []
    for group in groups:
        ranked = sorted((matches[code] for code in group["exams"]), key=lambda m: m["score"], reverse=True)
        counted = ranked[: group["required"]]
        covered = sum(1 for m in counted if m["status"] == "likely_covered")
        report.append({
            "name": group["name"],
            "kind": group["kind"],
            "required": group["required"],
            "likely_covered": covered,
            "possibly_needed": group["required"] - covered,
            "exams": ranked if group["kind"] == "compulsory" and group["required"] == len(group["exams"]) else counted,
        })
    return report
