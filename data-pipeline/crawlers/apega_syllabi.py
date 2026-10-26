"""Build APEGA's engineering exam syllabi (syllabi/apega_engineering.json) from APEGA's site.

    python crawlers/apega_syllabi.py           write the file
    python crawlers/apega_syllabi.py --check   build it and report differences only

The discipline web pages give each exam's code, title, description and the group rules
(e.g. "Compulsory exams – Six required"). The discipline assessment checklists (PDF)
give which Basic Studies exams are compulsory or optional for each discipline. The output
is reviewed by a person and committed like any other data change.

This syllabus is what the Board of Examiners uses when it assigns exams to applicants
whose degree is not accredited: Phase 2 matches applicants' courses against it.
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
import time
from datetime import date
from html import unescape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from crawlers.watch_sources import DELAY_SECONDS, http_fetch, robots_allows  # noqa: E402

OUTPUT = Path(__file__).resolve().parent.parent / "syllabi" / "apega_engineering.json"
SITE = "https://www.apega.ca"
PAGES = SITE + "/apply/membership/exams/technical/"
CHECKLISTS = SITE + "/docs/default-source/pdfs/technical-course-equivalents/"

# slug -> (name, checklist PDF path). The PDF paths carry APEGA's own version suffix.
DISCIPLINES = {
    "chemical-engineering": ("Chemical Engineering", "chemical-engineering-assessment-checklist.pdf?sfvrsn=3ecc8c69_4"),
    "civil-engineering": ("Civil Engineering", "civil-engineering-assessment-checklist.pdf?sfvrsn=da5b54ae_4"),
    "computer-engineering": ("Computer Engineering", "computer-engineering-assessment-checklist.pdf?sfvrsn=4ec4d6fe_4"),
    "electrical-engineering": ("Electrical Engineering", "electrical-engineering-assessment-checklist.pdf?sfvrsn=875e5d77_4"),
    "engineering-physics": ("Engineering Physics", "engineering-physics-assessment-checklist.pdf?sfvrsn=6014162d_4"),
    "environmental-engineering": ("Environmental Engineering", "environmental-engineering-assessment-checklist.pdf?sfvrsn=b433d9a2_4"),
    "geological-engineering": ("Geological Engineering", "geological-engineering-assessment-checklist.pdf?sfvrsn=f0aeefcd_4"),
    "geomatics-engineering": ("Geomatics Engineering", "geomatics-engineering-self-assessment-checklist.pdf?sfvrsn=f141bd42_4"),
    "industrial-engineering": ("Industrial Engineering", "industrial-engineering-assessment-checklist.pdf?sfvrsn=57d67d7b_4"),
    "mechanical-engineering": ("Mechanical Engineering", "mechanical-engineering-assessment-checklist.pdf?sfvrsn=76f9eb28_4"),
    "metallurgical-engineering": ("Metallurgical Engineering", "metallurgical-engineering-assessment-checklist.pdf?sfvrsn=1a510fcc_4"),
    "mining-mineral-processing-engineering": ("Mining and Mineral Processing Engineering", "mining-and-mineral-processing-engineering-self-assessment-checklist.pdf?sfvrsn=bbab66c5_4"),
    "petroleum-engineering": ("Petroleum Engineering", "petroleum-engineering-assessment-checklist.pdf?sfvrsn=a6fee4ba_4"),
    "software-engineering": ("Software Engineering", "software-engineering-self-assessment-checklist.pdf?sfvrsn=b02d9727_4"),
}
COMMON = {"preliminary-and-basic": "engineering-preliminary-and-basic-studies",
          "complementary": "complementary-studies"}

NUMBERS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9}
CODE = r"\d{2}-[A-Za-z]+ ?-[A-Z]{0,2}\d+(?:-[A-Z0-9]+)?"   # 16-Chem-A1, 04-BS-10, 20-Prelim-1, 18-Geol-B10-3, 17-Phys-A5-A


def _text(fragment: str) -> str:
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", fragment))).strip()


def _count(text: str) -> int:
    match = re.search(r"\b(one|two|three|four|five|six|seven|eight|nine|\d+)\b\s*(?:\)|required)", text, re.I) \
        or re.search(r"required[^a-z]*\b(one|two|three|four|five|six|seven|eight|nine|\d+)\b", text, re.I)
    if not match:
        raise ValueError(f"no required count in {text!r}")
    word = match.group(1).lower()
    return int(word) if word.isdigit() else NUMBERS[word]


def normalise_code(code: str) -> str:
    return re.sub(r"\s+", "", code)


def parse_page(html: str) -> dict:
    """Parse one APEGA syllabus page into {edition, groups: [...], exams: [...]}.

    A group is a heading (h2 "Group A", or h3 "Preliminary Exams") followed by a paragraph
    stating how many are required; exams are h3 headings starting with an exam code.
    """
    main = html[html.find("<main"):html.find("</main>")] or html
    headings = list(re.finditer(r"<(h[1-3])[^>]*>(.*?)</\1>", main, re.S))
    edition, groups, exams, current = None, [], [], None
    for i, h in enumerate(headings):
        tag, title = h.group(1), _text(h.group(2))
        body = main[h.end():headings[i + 1].start() if i + 1 < len(headings) else len(main)]
        paragraphs = [_text(p) for p in re.findall(r"<p[^>]*>(.*?)</p>", body, re.S)]
        paragraphs = [p for p in paragraphs if p]
        code = re.match(rf"({CODE})\s+(.*)", title)
        if tag == "h1" and re.search(r"\b(19|20)\d\d Edition", title):
            edition = title
        elif code:
            # "Electromagnetics (16-Elec-A7)": the same exam is listed under another discipline.
            same_as = [normalise_code(c) for c in re.findall(rf"\(\s*({CODE})\s*\)", code.group(2))]
            title = re.sub(rf"\s*[–-]?\s*\(\s*{CODE}\s*\)", "", code.group(2)).strip()
            exam = {"code": normalise_code(code.group(1)), "title": title,
                    "description": " ".join(paragraphs), "same_as": same_as}
            exams.append(exam)
            if current is not None:
                current["exams"].append(exam["code"])
        elif paragraphs and re.search(r"required", paragraphs[0], re.I):
            rule = paragraphs[0]
            current = {"name": title, "kind": "elective" if re.search(r"elective", rule, re.I) else "compulsory",
                       "required": _count(rule), "rule": rule, "exams": []}
            groups.append(current)
        elif tag == "h2" and re.search(r"Basic Studies", title):
            edition = edition or title
            current = {"name": title, "kind": "basic", "required": None, "rule": None, "exams": []}
            groups.append(current)
        elif tag in ("h1", "h2"):
            current = None
    return {"edition": edition, "groups": groups, "exams": exams}


def split_choice(group: dict) -> list[dict]:
    """Split "Six required: A1-A5 and one of A6-A7" into a compulsory and a choice group."""
    m = re.search(r"A(\d+)\s*-\s*A(\d+)\s+and\s+(\w+)\s+of\s+A(\d+)\s*-\s*A(\d+)", group["rule"] or "")
    if not m:
        return [group]
    a1, a2, n, c1, c2 = int(m.group(1)), int(m.group(2)), m.group(3).lower(), int(m.group(4)), int(m.group(5))
    number = lambda code: int(re.search(r"A(\d+)$", code).group(1))  # noqa: E731
    fixed = [c for c in group["exams"] if a1 <= number(c) <= a2]
    choice = [c for c in group["exams"] if c1 <= number(c) <= c2]
    return [dict(group, required=len(fixed), exams=fixed),
            dict(group, name=group["name"] + " (choice)", required=NUMBERS.get(n, 1), exams=choice)]


def parse_checklist(text: str) -> dict:
    """Basic Studies rules from a discipline checklist: compulsory codes, optional codes, optional count."""
    start = text.find("Basic Studies")
    optional_at = re.search(r"Optional Exams\s*\(\s*requires?\s*(\d+)\s*\)", text[start:], re.I)
    if start < 0 or not optional_at:
        raise ValueError("checklist has no Basic Studies section")
    compulsory = re.findall(r"04-BS-\d+", text[start:start + optional_at.start()])
    rest = text[start + optional_at.end():]
    optional = []
    for line in rest.splitlines():
        found = re.findall(r"04-BS-\d+", line)
        if found:
            optional += found
        elif re.search(CODE, line):
            break
    date_match = re.search(r"\((\d{2})\.(\d{2})\.(\d{4})\)", text)
    return {"compulsory": compulsory, "optional": optional, "optional_required": int(optional_at.group(1)),
            "checklist_date": f"{date_match.group(3)}-{date_match.group(1)}-{date_match.group(2)}" if date_match else None}


def pdf_text(data: bytes) -> str:
    from pypdf import PdfReader
    return "\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(data)).pages)


def fetch_bytes(url: str) -> bytes:
    import urllib.request
    from crawlers.watch_sources import USER_AGENT
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": USER_AGENT}), timeout=60) as r:
        return r.read()


def build(fetch_page=http_fetch, fetch_pdf=fetch_bytes, delay: float = DELAY_SECONDS, today: date | None = None) -> dict:
    today = today or date.today()
    if not robots_allows(PAGES, fetch_page):
        raise RuntimeError("robots.txt disallows the APEGA syllabus pages")
    sources, exams, common, disciplines = [], {}, {}, []

    def page(slug: str) -> dict:
        url = PAGES + slug
        response = fetch_page(url)
        if response.status != 200:
            raise RuntimeError(f"{url}: HTTP {response.status}")
        time.sleep(delay)
        parsed = parse_page(response.body)
        sources.append({"id": f"apega-syllabus-{slug}", "title": f"APEGA syllabus: {slug}", "url": url,
                        "retrieved_on": today.isoformat()})
        for exam in parsed["exams"]:
            exams.setdefault(exam["code"], dict(exam, source=f"apega-syllabus-{slug}"))
        return parsed

    for key, slug in COMMON.items():
        parsed = page(slug)
        common[key] = {"edition": parsed["edition"], "groups": [g for g in parsed["groups"]],
                       "source": f"apega-syllabus-{slug}"}

    for slug, (name, checklist) in DISCIPLINES.items():
        parsed = page(slug)
        groups = [part for g in parsed["groups"] for part in split_choice(g)]
        checklist_url = CHECKLISTS + checklist
        basic = parse_checklist(pdf_text(fetch_pdf(checklist_url)))
        time.sleep(delay)
        sources.append({"id": f"apega-checklist-{slug}", "title": f"APEGA assessment checklist: {name}",
                        "url": checklist_url, "retrieved_on": today.isoformat()})
        disciplines.append({"id": slug, "name": name, "edition": parsed["edition"], "groups": groups,
                            "basic_studies": dict(basic, source=f"apega-checklist-{slug}"),
                            "source": f"apega-syllabus-{slug}"})

    return {"regulator_id": "apega", "verified_on": today.isoformat(), "sources": sources,
            "preliminary": next(g for g in common["preliminary-and-basic"]["groups"] if g["kind"] != "basic")
            | {"source": common["preliminary-and-basic"]["source"]},
            "complementary": common["complementary"]["groups"][0] | {"source": common["complementary"]["source"]},
            "disciplines": disciplines,
            "exams": sorted(exams.values(), key=lambda e: e["code"])}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="report differences without writing")
    args = parser.parse_args(argv)
    result = build()
    text = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    old = OUTPUT.read_text(encoding="utf-8") if OUTPUT.exists() else None
    strip = lambda s: re.sub(r'"(verified_on|retrieved_on)": "[^"]+"', "", s or "")  # noqa: E731
    changed = strip(old) != strip(text)
    print(f"{len(result['disciplines'])} disciplines, {len(result['exams'])} exams; "
          f"{'changed' if changed else 'unchanged'} since the committed file.")
    if not args.check and changed:
        OUTPUT.parent.mkdir(exist_ok=True)
        OUTPUT.write_text(text, encoding="utf-8")
        print(f"Wrote {OUTPUT.relative_to(OUTPUT.parent.parent)}; review the diff before committing.")
    return 1 if (args.check and changed) else 0


if __name__ == "__main__":
    sys.exit(main())
