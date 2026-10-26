"""Validated shape of a regulator matrix (data-pipeline/matrices/*.json).

Every requirement, document, fee and timeline cites one of the matrix's own sources,
so each fact shown to an applicant can be traced back to the regulator's page.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

MATRICES_DIR = Path(__file__).parent / "matrices"


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Regulator(Strict):
    id: str = Field(pattern=r"^[a-z0-9-]+$")
    name: str
    short_name: str
    profession: str
    designation: str
    website: HttpUrl


class Source(Strict):
    id: str
    title: str
    url: HttpUrl
    retrieved_on: date
    publisher: str = "regulator"  # or the third party's name, e.g. an exam provider


class Pathway(Strict):
    id: str
    name: str
    summary: str
    source: str


class Requirement(Strict):
    id: str
    category: Literal["education", "exam", "experience", "language", "character",
                      "identity", "course", "insurance", "process"]
    title: str
    description: str
    pathways: list[str] = Field(min_length=1)
    source: str
    conditional: bool = False
    details: dict[str, Any] | None = None


class Document(Strict):
    id: str
    name: str
    description: str
    submitted_by: Literal["applicant", "third_party", "issuing_institution"]
    source: str
    conditional: bool = False


class Fee(Strict):
    id: str
    name: str
    amount: float = Field(gt=0)
    currency: Literal["CAD", "USD"]
    gst: Literal["included", "excluded", "not_applicable", "not_stated"]
    refundable: bool
    payee: str
    conditional: bool = False
    period: str | None = None
    effective_from: date | None = None
    effective_until: date | None = None
    source: str

    @model_validator(mode="after")
    def dates_in_order(self) -> "Fee":
        if self.effective_from and self.effective_until and self.effective_from > self.effective_until:
            raise ValueError(f"fee {self.id} ends before it starts")
        return self


class Timeline(Strict):
    id: str
    name: str
    max_days: int | None = Field(default=None, gt=0)
    business_days: bool = False
    description: str | None = None
    source: str


class Competency(Strict):
    code: str
    category: str
    name: str
    min_level: int | None = Field(default=None, ge=1, le=5)
    mandatory: bool = False


class CompetencyCategory(Strict):
    name: str
    min_average: float = Field(ge=0, le=5)
    source: str


class CompetencyScale(Strict):
    min: int
    max: int
    source: str


class Matrix(Strict):
    regulator: Regulator
    verified_on: date
    sources: list[Source] = Field(min_length=1)
    pathways: list[Pathway] = Field(min_length=1)
    requirements: list[Requirement] = Field(min_length=1)
    documents: list[Document]
    fees: list[Fee]
    timelines: list[Timeline]
    competencies: list[Competency]
    competency_source: str | None = None
    competency_categories: list[CompetencyCategory] = []
    competency_scale: CompetencyScale | None = None
    open_questions: list[str] = []

    @model_validator(mode="after")
    def references_resolve(self) -> "Matrix":
        for name, items in (("sources", self.sources), ("pathways", self.pathways),
                            ("requirements", self.requirements), ("documents", self.documents),
                            ("fees", self.fees), ("timelines", self.timelines)):
            ids = [item.id for item in items]
            dupes = sorted({i for i in ids if ids.count(i) > 1})
            if dupes:
                raise ValueError(f"duplicate {name} ids: {dupes}")
        codes = [c.code for c in self.competencies]
        if len(codes) != len(set(codes)):
            raise ValueError("duplicate competency codes")

        source_ids = {s.id for s in self.sources}
        cited = [p.source for p in self.pathways] + [r.source for r in self.requirements] \
            + [d.source for d in self.documents] + [f.source for f in self.fees] \
            + [t.source for t in self.timelines]
        if self.competencies:
            if not self.competency_source:
                raise ValueError("competencies need a competency_source")
            cited.append(self.competency_source)
        cited += [c.source for c in self.competency_categories]
        if self.competency_scale:
            cited.append(self.competency_scale.source)
        unknown = sorted(set(cited) - source_ids)
        if unknown:
            raise ValueError(f"unknown source ids: {unknown}")

        pathway_ids = {p.id for p in self.pathways}
        for r in self.requirements:
            missing = set(r.pathways) - pathway_ids
            if missing:
                raise ValueError(f"requirement {r.id} names unknown pathways {sorted(missing)}")

        for c in self.competencies:
            if c.mandatory and c.min_level is None:
                raise ValueError(f"mandatory competency {c.code} has no min_level")
        used = {c.category for c in self.competencies}
        unused = sorted({c.name for c in self.competency_categories} - used)
        if unused:
            raise ValueError(f"competency_categories with no competencies: {unused}")

        for s in self.sources:
            if s.retrieved_on > self.verified_on:
                raise ValueError(f"source {s.id} retrieved after verified_on")
        return self


def load_matrix(path: Path) -> Matrix:
    return Matrix.model_validate(json.loads(path.read_text(encoding="utf-8")))


def load_all(directory: Path = MATRICES_DIR) -> list[Matrix]:
    matrices = [load_matrix(p) for p in sorted(directory.glob("*.json"))]
    ids = [m.regulator.id for m in matrices]
    if len(ids) != len(set(ids)):
        raise ValueError(f"two matrices share a regulator id: {ids}")
    return matrices


# ---- Exam syllabi (syllabi/*.json, built by crawlers/apega_syllabi.py) ----

SYLLABI_DIR = Path(__file__).parent / "syllabi"


class SyllabusGroup(Strict):
    name: str
    kind: Literal["compulsory", "elective"]
    required: int = Field(ge=1)
    rule: str
    exams: list[str] = Field(min_length=1)


class CommonGroup(SyllabusGroup):
    source: str


class BasicStudies(Strict):
    compulsory: list[str]
    optional: list[str]
    optional_required: int = Field(ge=0)
    checklist_date: date | None = None
    source: str


class Discipline(Strict):
    id: str
    name: str
    edition: str | None
    groups: list[SyllabusGroup] = Field(min_length=1)
    basic_studies: BasicStudies
    source: str


class SyllabusExam(Strict):
    code: str
    title: str
    description: str = Field(min_length=1)
    same_as: list[str] = []
    source: str


class Syllabus(Strict):
    regulator_id: str
    verified_on: date
    sources: list[Source] = Field(min_length=1)
    preliminary: CommonGroup
    complementary: CommonGroup
    disciplines: list[Discipline] = Field(min_length=1)
    exams: list[SyllabusExam] = Field(min_length=1)

    @model_validator(mode="after")
    def references_resolve(self) -> "Syllabus":
        codes = [e.code for e in self.exams]
        if len(codes) != len(set(codes)):
            raise ValueError("duplicate exam codes")
        known, source_ids = set(codes), {s.id for s in self.sources}
        groups = [self.preliminary, self.complementary] + [g for d in self.disciplines for g in d.groups]
        for g in groups:
            if g.required > len(g.exams):
                raise ValueError(f"group {g.name!r} requires {g.required} of {len(g.exams)} exams")
            if set(g.exams) - known:
                raise ValueError(f"group {g.name!r} lists unknown exams {sorted(set(g.exams) - known)}")
        for d in self.disciplines:
            b = d.basic_studies
            if set(b.compulsory + b.optional) - known:
                raise ValueError(f"{d.id} basic studies list unknown exams")
            if b.optional_required > len(b.optional):
                raise ValueError(f"{d.id} requires more optional basic studies than it lists")
        cited = [self.preliminary.source, self.complementary.source] + [e.source for e in self.exams] \
            + [x for d in self.disciplines for x in (d.source, d.basic_studies.source)]
        if set(cited) - source_ids:
            raise ValueError(f"unknown source ids: {sorted(set(cited) - source_ids)}")
        return self


def load_syllabus(path: Path) -> Syllabus:
    return Syllabus.model_validate(json.loads(path.read_text(encoding="utf-8")))
