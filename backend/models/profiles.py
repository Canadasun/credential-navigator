"""What an applicant tells us. Every answer is optional: unknown answers become "to confirm"
items in the roadmap instead of guesses."""
from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Answers(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ApegaProfile(Answers):
    experience_months: int | None = Field(None, ge=0, le=720, description="Engineering work experience, in months")
    canadian_citizen_or_pr: bool | None = None
    ceab_accredited_degree: bool | None = Field(None, description="Degree from a CEAB-accredited program")
    wes_icap_received: bool | None = Field(None, description="WES Course-by-Course ICAP report sent to APEGA")
    nppe_passed: bool | None = None
    english_competent: bool | None = None
    references_ready: bool | None = None


class EnglishResult(Answers):
    test: Literal["IELTS Academic", "CELBAN"]
    taken_on: date
    scores: dict[Literal["listening", "writing", "reading", "speaking", "overall"], float]


class CrnaProfile(Answers):
    nclex_passed: bool | None = None
    credential_report: Literal["nnas", "eca", "none"] | None = Field(
        None, description="NNAS advisory report, an education credential assessment from an accepted provider, or none")
    nnas_rating: Literal["comparable", "somewhat comparable", "not comparable"] | None = None
    practice_hours_last_2_years: int | None = Field(None, ge=0)
    practice_hours_last_5_years: int | None = Field(None, ge=0)
    qualifying_program_last_5_years: bool | None = Field(
        None, description="Approved nursing program, RNCCAP, bridging or re-entry program completed in the last 5 practice years")
    english: EnglishResult | None = None
    english_exemption: bool | None = Field(None, description="Meets one of the CRNA's English exemptions")
    criminal_record_check_done: bool | None = None
    jurisprudence_done: bool | None = None
    sexual_abuse_course_done: bool | None = None
    liability_protection: bool | None = None
