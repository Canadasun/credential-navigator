"""APEGA academic gap analysis.

Uploads are read in memory and discarded after the response: nothing is stored yet
(storage, consent and retention come with S3 and user accounts).
"""
from __future__ import annotations

from dataclasses import replace

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from core.config import DISCLAIMER, MAX_UPLOAD_BYTES, connection
from services import regulatory_repo
from services.course_extraction import extract_courses
from services.matching import evaluate_groups, match_exams
from services.pdf_text import UnreadableDocument, extract_text

router = APIRouter(prefix="/apega", tags=["APEGA"])


@router.get("/disciplines")
def list_disciplines() -> list[dict]:
    with connection() as conn:
        return regulatory_repo.disciplines(conn, "apega")


def analyse(courses: list[dict], discipline: str) -> dict:
    with connection() as conn:
        groups = regulatory_repo.discipline_groups(conn, "apega", discipline)
        if groups is None:
            raise HTTPException(404, f"Unknown discipline {discipline!r}. See GET /apega/disciplines.")
        corpus = regulatory_repo.all_exams(conn, "apega")
        syllabus_url = regulatory_repo.source_url(conn, "apega", discipline)
    priority = {}
    for group in groups:
        for code in group["exams"]:
            # Exams every applicant must cover get first claim on courses.
            tier = 0 if group["kind"] == "compulsory" and group["required"] == len(group["exams"]) else 1
            priority[code] = min(tier, priority.get(code, tier))
    exams = [replace(e, priority=priority[e.code]) for e in corpus if e.code in priority]
    matches = match_exams(courses, exams, corpus)
    report = evaluate_groups(groups, matches)
    return {
        "disclaimer": DISCLAIMER,
        "discipline": discipline,
        "syllabus_source": syllabus_url,
        "courses_found": courses,
        "groups": report,
        "notes": notes(courses),
        "summary": {
            "courses_found": len(courses),
            "exams_required": sum(g["required"] for g in report),
            "likely_covered": sum(g["likely_covered"] for g in report),
            "possibly_needed": sum(g["possibly_needed"] for g in report),
        },
    }


def notes(courses: list[dict]) -> list[str]:
    out = []
    without = sum(1 for c in courses if len(c.get("description") or "") < 40)
    if without > len(courses) / 2:
        out.append("Most courses have only a title. Upload the course descriptions or syllabi as well: "
                   "titles alone give a rough comparison.")
    out.append("Each course counts toward one exam only. A course that covers two subjects may show one "
               "of them as a possible gap.")
    return out


@router.post("/analysis")
async def analyse_upload(discipline: str = Form(...), file: UploadFile = File(...)) -> dict:
    data = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "The file is larger than 10 MB.")
    try:
        text = extract_text(data)
    except UnreadableDocument as error:
        raise HTTPException(422, str(error)) from error
    courses = [c.as_dict() for c in extract_courses(text)]
    if not courses:
        raise HTTPException(422, "No courses were found. The document needs one course per line, "
                                 "starting with a course code such as 'MATH 201'.")
    return analyse(courses, discipline)
