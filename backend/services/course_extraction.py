"""Find courses in transcript or syllabus text without an LLM.

A course starts on a line that begins with a course code ("CHEM 101", "MATH-201",
"EE3014"). The rest of that line is the title, optionally followed by credits and a grade
(transcripts). Lines after it, until the next course line, are its description
(course-description documents). Anything before the first course line is ignored.

This handles text-based documents laid out one course per line. Messier layouts are
what the optional LLM extractor is for.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

COURSE_LINE = re.compile(
    r"^\s*(?P<code>[A-Z]{2,6}[ \-]?\d{2,4}[A-Z]?)\b[\s:.\-–]+"
    r"(?P<title>[A-Za-z(][^\t]*?)"
    r"(?:\s+(?P<credits>\d{1,2}(?:\.\d{1,2})?))?"
    r"(?:\s*(?P<grade>(?<=\d)[A-F][+-]?|(?<=\s)[A-F][+-]?|(?<=\s)\d{1,3}(?:\.\d)?%?|(?<=\s)[PS]))?\s*$")
# OCR commonly reads a trailing "+" as "t" or "‡" ("Bt" for "B+").
OCR_PLUS = re.compile(r"(?<=\d)(\s*[A-F])[t‡](?=\s*$)")
# Headings and footers that are not part of a course description.
NOISE = re.compile(r"^\s*(page \d+|term|semester|year \d|cumulative|gpa|total|official transcript)\b", re.I)


@dataclass
class Course:
    code: str
    title: str
    credits: float | None = None
    grade: str | None = None
    description: str = ""
    lines: list[str] = field(default_factory=list, repr=False)

    def as_dict(self) -> dict:
        return {"code": self.code, "title": self.title, "credits": self.credits,
                "grade": self.grade, "description": self.description}


def extract_courses(text: str) -> list[Course]:
    courses: list[Course] = []
    current: Course | None = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        match = COURSE_LINE.match(OCR_PLUS.sub(r"\1+", line))
        if match and len(match.group("title").split()) <= 14:
            code = re.sub(r"[ \-]", " ", match.group("code")).strip()
            code = re.sub(r"(?<=[A-Z])(?=\d)", " ", code) if " " not in code else code
            current = Course(code=code, title=match.group("title").strip(" .:-"),
                             credits=float(match.group("credits")) if match.group("credits") else None,
                             grade=match.group("grade"))
            courses.append(current)
        elif current is not None and not NOISE.match(line):
            current.lines.append(line)
    for course in courses:
        course.description = re.sub(r"\s+", " ", " ".join(course.lines)).strip()
    # The same course listed twice (e.g. a repeated attempt) keeps the longer description.
    unique: dict[str, Course] = {}
    for course in courses:
        if course.code not in unique or len(course.description) > len(unique[course.code].description):
            unique[course.code] = course
    return list(unique.values())
