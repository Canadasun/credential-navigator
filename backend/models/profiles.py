"""What an applicant tells us. Every answer is optional: unknown answers become "to confirm"
items in the roadmap instead of guesses."""
from __future__ import annotations

from datetime import date
import math
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


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

    @model_validator(mode="after")
    def validate_test(self):
        if self.taken_on > date.today():
            raise ValueError("Date taken cannot be in the future.")
        maximum, step = (9, 0.5) if self.test == "IELTS Academic" else (12, 1)
        if self.test == "CELBAN" and "overall" in self.scores:
            raise ValueError("CELBAN uses four skill levels, not an overall score.")
        for part, score in self.scores.items():
            if not math.isfinite(score) or not 0 <= score <= maximum or score % step:
                raise ValueError(f"{part}: {self.test} scores must be between 0 and {maximum} in steps of {step}.")
        return self


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

    @model_validator(mode="after")
    def single_english_basis(self):
        if self.english is not None and self.english_exemption is True:
            raise ValueError("Choose English test results or an exemption, not both.")
        return self


OET_GRADES = ("E", "D", "C", "C+", "B", "A")


class PharmacyEnglishResult(Answers):
    """IELTS Academic bands (0-9 in half bands) or OET letter grades, from one sitting."""
    test: Literal["IELTS Academic", "OET"]
    taken_on: date
    scores: dict[Literal["listening", "writing", "reading", "speaking"], float | str]

    @model_validator(mode="after")
    def validate_test(self):
        if self.taken_on > date.today():
            raise ValueError("Date taken cannot be in the future.")
        for part, score in self.scores.items():
            if self.test == "OET":
                if score not in OET_GRADES:
                    raise ValueError(f"{part}: OET grades are A, B, C+, C, D or E.")
            elif isinstance(score, str) or not math.isfinite(score) or not 0 <= score <= 9 or score % 0.5:
                raise ValueError(f"{part}: IELTS scores must be between 0 and 9 in steps of 0.5.")
        return self


class AcpProfile(Answers):
    us_acpe_pharmd: bool | None = Field(None, description="Doctor of Pharmacy from an ACPE-accredited US program")
    gateway_enrolled: bool | None = Field(None, description="Enrolled in Pharmacists' Gateway Canada")
    document_evaluation_done: bool | None = Field(None, description="PEBC Document Evaluation approved")
    english: PharmacyEnglishResult | None = None
    english_exemption: bool | None = None
    pebc_part1_passed: bool | None = None
    pebc_part2_passed: bool | None = None
    pebc_both_first_attempt: bool | None = Field(None, description="Both PEBC parts passed on the first attempt")
    dcpp_completed: bool | None = Field(None, description="University of Alberta DCPP (or former CCPP) completed")
    criminal_record_check_done: bool | None = None
    provisional_registered: bool | None = Field(None, description="On ACP's provisional (intern) register")
    jurisprudence_done: bool | None = Field(None, description="Jurisprudence module done and exam passed")
    spt_experiences_completed: int | None = Field(None, ge=0, le=10,
                                                  description="Completed SPT practical experiences (320+ hours each)")
    liability_insurance: bool | None = None

    @model_validator(mode="after")
    def consistent(self):
        if self.english is not None and self.english_exemption is True:
            raise ValueError("Choose English test results or an exemption, not both.")
        if self.pebc_both_first_attempt and not (self.pebc_part1_passed and self.pebc_part2_passed):
            raise ValueError("Passing both PEBC parts on the first attempt means both parts are passed.")
        return self


CipsEducation = Literal[
    "accredited-4-year-university-cs", "accredited-4-year-university-interdisciplinary",
    "accredited-3-year-university-cs", "non-accredited-4-year-university-cs", "non-accredited-3-year-university-cs",
    "accredited-3-year-college", "accredited-2-year-college", "non-accredited-3-year-college",
    "non-accredited-2-year-college", "accredited-post-graduate-it", "non-it-or-none"]


class CipsProfile(Answers):
    education: CipsEducation | None = Field(None, description="Highest IT education; 'accredited' means CIPS-accredited")
    it_experience_years: float | None = Field(None, ge=0, le=60, description="Years of IT professional work")
    sfia_level_3: bool | None = Field(None, description="Currently working at SFIA responsibility level 3 or higher")
    hours_last_12_months: int | None = Field(None, ge=0, le=8784, description="IT work hours in the last 12 months")
    cips_member: bool | None = None
    transcripts_sent: bool | None = None
    references_ready: bool | None = None
    skills_assessment_done: bool | None = None
    recent_graduate: bool | None = Field(None, description="Graduated in the last 5 years with under 5 years of IT work")
