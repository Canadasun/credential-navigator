"""Personal licensing roadmap: route, requirement status, costs and timelines.

Requirements, thresholds (hours, test scores, months) and fees come from the regulator
data in the database; this module only compares them with the applicant's answers.
Unknown answers give "to_confirm", never a guess.

Statuses: done, to_do, to_confirm (we need an answer), may_apply (only if the
regulator asks for it), not_needed.
"""
from __future__ import annotations

from calendar import monthrange
from datetime import date

from models.profiles import OET_GRADES, AcpProfile, ApegaProfile, CipsProfile, CrnaProfile
from services import regulatory_repo

DONE, TO_DO, TO_CONFIRM, MAY_APPLY, NOT_NEEDED = "done", "to_do", "to_confirm", "may_apply", "not_needed"
IN_APPLICATION = "Declared or provided in the application itself."


def _yes_no(value: bool | None, yes: str = "", no: str = "") -> tuple[str, str]:
    if value is None:
        return TO_CONFIRM, ""
    return (DONE, yes) if value else (TO_DO, no)


# ---------------------------------------------------------------- APEGA

def apega_pathway(p: ApegaProfile) -> str | None:
    if p.experience_months is None:
        return None
    if p.experience_months < 48:
        return "member-in-training"
    if p.canadian_citizen_or_pr is None:
        return None
    return "professional-member" if p.canadian_citizen_or_pr else "licensee"


def apega_status(req: dict, p: ApegaProfile) -> tuple[str, str]:
    rid = req["id"]
    if rid == "academic":
        if p.ceab_accredited_degree:
            return DONE, "CEAB-accredited degree."
        if p.ceab_accredited_degree is False:
            if p.wes_icap_received:
                return TO_DO, ("WES report received; the Board of Examiners will compare your degree with the "
                               "syllabus. Use the academic gap analysis to see which exams may be assigned.")
            return TO_DO, "Order a WES Course-by-Course ICAP report, the only evaluation APEGA accepts."
        return TO_CONFIRM, "Is your degree from a CEAB-accredited program?"
    if rid == "assigned-exams":
        if p.ceab_accredited_degree:
            return NOT_NEEDED, "Not expected for an accredited degree."
        return MAY_APPLY, "Depends on the Board of Examiners' review of your degree."
    if rid == "experience":
        needed = (req["details"] or {}).get("months", 48)
        if p.experience_months is None:
            return TO_CONFIRM, f"How many months of engineering experience do you have? {needed} are required."
        if p.experience_months >= needed:
            return DONE, f"{p.experience_months} months (at least {needed} required)."
        return TO_DO, f"{needed - p.experience_months} more months needed; you can apply as a member-in-training now."
    if rid == "competencies":
        return TO_DO, "Describe your experience against the 22 competencies in APEGA's assessment tool."
    if rid == "references":
        return _yes_no(p.references_ready, "References and validators lined up.", "Line up references and validators.")
    if rid == "nppe":
        return _yes_no(p.nppe_passed, "Passed.", "Write it once your application is in progress.")
    if rid == "english":
        return _yes_no(p.english_competent)
    if rid == "citizenship":
        return _yes_no(p.canadian_citizen_or_pr, "", "Not required for the licensee route.")
    return _default(req)


def _default(req: dict) -> tuple[str, str]:
    return TO_DO, IN_APPLICATION if req["category"] in ("character", "identity") else ""


def apega_fees(p: ApegaProfile, pathway: str | None, fees: dict, today: date) -> list[tuple[str, str, str]]:
    """(fee id, status, why) for fees that apply to this applicant."""
    out = []
    if pathway in (None, "professional-member", "licensee"):
        out.append(("application-new", TO_DO, "Application fee."))
    if not p.nppe_passed and pathway != "member-in-training":
        out.append(("nppe", TO_DO, "Per attempt."))
    if not p.ceab_accredited_degree:
        out += [("fe-apega", MAY_APPLY, "If the Board assigns the FE exam."),
                ("fe-ncees", MAY_APPLY, "If the Board assigns the FE exam."),
                ("technical-exam", MAY_APPLY, "Per technical exam the Board assigns.")]
    return out


# ---------------------------------------------------------------- CRNA

def crna_pathway(p: CrnaProfile) -> str | None:
    if p.nclex_passed is None:
        return None
    return "nclex-passed" if p.nclex_passed else "credential-recognition"


def _currency(details: dict, p: CrnaProfile) -> tuple[str, str]:
    options = details.get("any_of", [])
    unknown, shortfalls = False, []
    for option in options:
        if option["type"] == "practice_hours":
            hours = p.practice_hours_last_2_years if option["within_practice_years"] == 2 else p.practice_hours_last_5_years
            if hours is None:
                unknown = True
            elif hours >= option["hours"]:
                return DONE, f"{hours} practice hours in the last {option['within_practice_years']} practice years."
            else:
                shortfalls.append(f"{option['hours'] - hours} more hours within {option['within_practice_years']} years")
        elif option["type"] == "program":
            if p.qualifying_program_last_5_years:
                return DONE, "Qualifying program completed in the last 5 practice years."
            if p.qualifying_program_last_5_years is None:
                unknown = True
    if unknown:
        return TO_CONFIRM, "How many nursing practice hours do you have in the last 2 and 5 years?"
    return TO_DO, ("Not met yet: " + " or ".join(shortfalls) +
                   ", or a bridging, re-entry or competence assessment program.")


def _anniversary(day: date, years: int) -> date:
    """The same date `years` later; 29 February becomes 28 February in a non-leap year."""
    year = day.year + years
    return day.replace(year=year, day=min(day.day, monthrange(year, day.month)[1]))


def _below(score: float | str | None, minimum: float | str) -> bool:
    """True when a band is missing or under the minimum; OET letter grades are ranked E to A."""
    if score is None:
        return True
    if isinstance(minimum, str):
        return not isinstance(score, str) or OET_GRADES.index(score) < OET_GRADES.index(minimum)
    return isinstance(score, str) or score < minimum


def _english(details: dict, p: CrnaProfile | AcpProfile, today: date) -> tuple[str, str]:
    if p.english_exemption:
        return DONE, "Exemption."
    if p.english is None:
        tests = " or ".join(t["name"] for t in details.get("tests", []))
        return (TO_DO, f"Take {tests}.") if p.english_exemption is False else (TO_CONFIRM, "")
    test = next((t for t in details.get("tests", []) if t["name"] == p.english.test), None)
    if test is None:
        return TO_DO, f"{p.english.test} is not accepted."
    expires = _anniversary(p.english.taken_on, test["valid_years"])
    low = [f"{part} {p.english.scores.get(part, 'missing')} (needs {minimum})"
           for part, minimum in test["min_scores"].items() if _below(p.english.scores.get(part), minimum)]
    if low:
        return TO_DO, "Below the minimum: " + ", ".join(low) + "."
    if expires < today:
        return TO_DO, f"Scores meet the minimums but expired on {expires.isoformat()}."
    return DONE, f"{test['name']} scores meet the minimums; valid until {expires.isoformat()}."


def crna_status(req: dict, p: CrnaProfile, today: date) -> tuple[str, str]:
    rid, details = req["id"], req["details"] or {}
    if rid == "credential-assessment" or rid == "post-secondary":
        if p.credential_report == "eca":
            return DONE, "Education credential assessment from an accepted provider."
        if p.credential_report == "nnas":
            if p.nnas_rating in ("comparable", "somewhat comparable"):
                return DONE, f"NNAS report rated {p.nnas_rating}."
            if p.nnas_rating == "not comparable":
                return TO_DO, "Not equivalent: the CRNA refers the application to the registrar."
            return TO_CONFIRM, "What rating did the NNAS report give your education?"
        if p.credential_report == "none":
            providers = ", ".join(details.get("accepted_providers", [])) or "an accepted provider"
            return TO_DO, f"Get an assessment from {providers}, or an NNAS advisory report."
        return TO_CONFIRM, ""
    if rid == "nclex-rn":
        return _yes_no(p.nclex_passed, "Passed.", "Request to write it once your education is recognized.")
    if rid == "currency-of-practice":
        return _currency(details, p)
    if rid == "english":
        return _english(details, p, today)
    if rid == "criminal-record-check":
        return _yes_no(p.criminal_record_check_done)
    if rid == "jurisprudence":
        return _yes_no(p.jurisprudence_done)
    if rid == "sexual-abuse-course":
        return _yes_no(p.sexual_abuse_course_done)
    if rid == "liability":
        return _yes_no(p.liability_protection, "", "Buy it from the Canadian Nurses Protective Society.")
    return _default(req)


def _effective(fees: dict, ids: list[str], today: date) -> str | None:
    """The first of several dated versions of a fee that is in effect today."""
    for fee_id in ids:
        fee = fees.get(fee_id)
        if fee and (fee["effective_from"] is None or fee["effective_from"] <= today) \
                and (fee["effective_until"] is None or today <= fee["effective_until"]):
            return fee_id
    return None


def crna_fees(p: CrnaProfile, pathway: str | None, fees: dict, today: date) -> list[tuple[str, str, str]]:
    out = [("account-creation", TO_DO, "One-time."), ("rn-permit", TO_DO, "Once all requirements are met.")]
    if not p.nclex_passed:
        nclex = _effective(fees, ["nclex-registration", "nclex-registration-2027"], today)
        if nclex:
            out.append((nclex, TO_DO, "Registration with Pearson VUE."))
        out.append(("nclex-international-scheduling", MAY_APPLY, "If you test outside Canada."))
    if p.credential_report in (None, "none"):
        out.append(("nnas-application", MAY_APPLY, "If you use NNAS; accepted assessment providers charge their own fees."))
    return out


# ---------------------------------------------------------------- ACP

def acp_pathway(p: AcpProfile) -> str | None:
    if p.us_acpe_pharmd is None:
        return None
    return "us-pharmd" if p.us_acpe_pharmd else "international"


def _after_provisional(p: AcpProfile, detail: str) -> str:
    return detail if p.provisional_registered else detail + " This comes after you join the provisional register."


def acp_status(req: dict, p: AcpProfile, today: date) -> tuple[str, str]:
    rid, details = req["id"], req["details"] or {}
    if rid == "gateway":
        return _yes_no(p.gateway_enrolled, "Enrolled.", "Enrol and choose the Alberta College of Pharmacy.")
    if rid == "document-evaluation":
        which = "US Document Evaluation" if p.us_acpe_pharmd else "Document Evaluation"
        return _yes_no(p.document_evaluation_done, f"PEBC {which} approved.",
                       f"Apply to PEBC for the {which} once you have your Gateway ID number.")
    if rid == "english":
        if p.us_acpe_pharmd and p.english is None and p.english_exemption is None:
            return NOT_NEEDED, "Not usually needed after an English-taught ACPE program, unless ACP asks."
        return _english(details, p, today)
    if rid == "provisional-exam":
        if p.provisional_registered or p.pebc_part1_passed or p.pebc_part2_passed or p.dcpp_completed:
            return DONE, "PEBC exam part or DCPP completed."
        if p.pebc_part1_passed is False and p.pebc_part2_passed is False and p.dcpp_completed is False:
            return TO_DO, "Pass PEBC Part I (MCQ) or complete the DCPP to join the provisional register."
        return TO_CONFIRM, "Have you passed a PEBC Qualifying Exam part or completed the DCPP?"
    if rid == "criminal-record-check":
        return _yes_no(p.criminal_record_check_done, "", "Order an Enhanced Police Information Check; it must be "
                                                         "less than six months old when you apply.")
    if rid == "jurisprudence":
        status, detail = _yes_no(p.jurisprudence_done, "Module done and exam passed.",
                                 "Complete the module and pass the exam before starting SPT.")
        return status, _after_provisional(p, detail) if status == TO_DO else detail
    if rid == "spt":
        needed = details.get("min_experiences", 2)
        hours = details.get("min_hours_each", 320)
        if p.spt_experiences_completed is None:
            return TO_CONFIRM, f"How many SPT practical experiences have you completed? {needed} are required."
        if p.spt_experiences_completed >= needed:
            return DONE, f"{p.spt_experiences_completed} practical experiences completed."
        left = needed - p.spt_experiences_completed
        return TO_DO, _after_provisional(p, f"{left} more practical experience{'s' if left > 1 else ''} of at "
                                            f"least {hours} hours, each with a different preceptor and site.")
    if rid == "pebc-qualifying":
        if p.pebc_part1_passed and p.pebc_part2_passed:
            return DONE, "Both parts passed; results must be less than three years old when you apply."
        if p.pebc_part1_passed is None or p.pebc_part2_passed is None:
            return TO_CONFIRM, "Which PEBC Qualifying Exam parts have you passed?"
        missing = [name for name, passed in (("Part I (MCQ)", p.pebc_part1_passed),
                                             ("Part II (OSCE)", p.pebc_part2_passed)) if not passed]
        detail = "Still to pass: " + " and ".join(missing) + "."
        if not p.pebc_part1_passed:
            detail += " From January 2027, Part I comes before Part II unless you passed the Evaluating Exam."
        return TO_DO, detail
    if rid == "dcpp":
        if p.dcpp_completed:
            return DONE, "Completed."
        if p.pebc_both_first_attempt:
            return NOT_NEEDED, "Exempt: both PEBC parts passed on the first attempt."
        if p.dcpp_completed is False:
            return TO_DO, "Required unless you pass both PEBC parts on your first attempt."
        return TO_CONFIRM, "Have you completed the DCPP? It's required unless you pass both PEBC parts on your first attempt."
    if rid == "liability":
        return _yes_no(p.liability_insurance, "", "Needed before the clinical register: at least $2 million, "
                                                  "in your own name.")
    return _default(req)


def acp_fees(p: AcpProfile, pathway: str | None, fees: dict, today: date) -> list[tuple[str, str, str]]:
    out = []
    if not p.gateway_enrolled:
        out.append(("gateway-enrolment", TO_DO, "One-time; plus applicable taxes."))
    if not p.document_evaluation_done:
        fee = "pebc-us-document-evaluation" if pathway == "us-pharmd" else "pebc-document-evaluation"
        out.append((fee, TO_DO, "One-time; valid five years."))
    if not p.pebc_part1_passed:
        out.append(("pebc-part1", TO_DO, "Per attempt."))
    if not p.pebc_part2_passed:
        out.append(("pebc-part2", TO_DO, "Per attempt."))
    if not p.provisional_registered:
        out.append(("acp-registration", TO_DO, "When you join the provisional register."))
    out += [("acp-permit", TO_DO, "Clinical pharmacist permit, renewed each year by June 30."),
            ("acp-permit-prorated", MAY_APPLY, "Instead of the full permit if you join between January 1 and June 30."),
            ("acp-jurisprudence-rechallenge", MAY_APPLY, "If you need to rewrite the jurisprudence exam.")]
    return out


# ---------------------------------------------------------------- CIPS (I.S.P., voluntary)

def cips_pathway(p: CipsProfile) -> str | None:
    if p.education is None:
        return None
    return "experience-only" if p.education == "non-it-or-none" else "education"


def cips_status(req: dict, p: CipsProfile, today: date) -> tuple[str, str]:
    rid, details = req["id"], req["details"] or {}
    if rid == "membership":
        return _yes_no(p.cips_member, "Member.", "Join CIPS before you apply.")
    if rid == "transcripts":
        return _yes_no(p.transcripts_sent, "", "Ask your institution, or an assessment centre such as WES, to send "
                                               "them to CIPS directly.")
    if rid == "experience":
        if p.education is None:
            return TO_CONFIRM, "What is your highest IT education? It sets the years of experience needed."
        needed = details.get("years_by_education", {}).get(p.education, details.get("experience_only_years", 8))
        if p.it_experience_years is None:
            return TO_CONFIRM, f"How many years of IT work do you have? {needed} are needed with your education."
        if p.it_experience_years < needed:
            gap = needed - p.it_experience_years
            return TO_DO, f"{gap:g} more year{'' if gap == 1 else 's'} of IT work needed ({needed} in total)."
        if p.sfia_level_3 is False:
            return TO_DO, f"{p.it_experience_years:g} years is enough, but your current role must be at SFIA level 3 or higher."
        if p.sfia_level_3 is None:
            return TO_CONFIRM, f"{p.it_experience_years:g} years is enough. Is your current role at SFIA level 3 or higher?"
        return DONE, f"{p.it_experience_years:g} years (at least {needed} needed), working at SFIA level 3 or higher."
    if rid == "recent-hours":
        hours = details.get("hours", 1000)
        if p.hours_last_12_months is None:
            return TO_CONFIRM, f"How many hours of IT work have you done in the last 12 months? {hours} are needed."
        if p.hours_last_12_months >= hours:
            return DONE, f"{p.hours_last_12_months} hours in the last 12 months."
        return TO_DO, f"{hours - p.hours_last_12_months} more hours of IT work within 12 months."
    if rid == "references":
        return _yes_no(p.references_ready, "", "Ask for letters covering your last two years of work.")
    if rid == "skills-assessment":
        return _yes_no(p.skills_assessment_done, "", "Update your résumé and complete the SFIA self-assessment.")
    return _default(req)


def cips_fees(p: CipsProfile, pathway: str | None, fees: dict, today: date) -> list[tuple[str, str, str]]:
    if p.recent_graduate:
        out = [("review-fee-recent-graduate", TO_DO, "One-time, instead of the standard review fee.")]
    else:
        out = [("review-fee", TO_DO, "One-time, before you apply.")]
        if p.recent_graduate is None:
            out.append(("review-fee-recent-graduate", MAY_APPLY, "Instead of the standard fee if you graduated in "
                                                                 "the last 5 years with under 5 years of IT work."))
    return out + [("certified-member-fee", TO_DO, "Each year once certified; replaces the regular member fee.")]


# ---------------------------------------------------------------- shared

def cost_notes(regulator_id: str, pathway_id: str | None) -> list[str]:
    notes = ["Third-party costs not listed here: credential evaluation (WES, NNAS or another provider), "
             "English tests, document translation and courier fees."]
    if regulator_id == "apega" and pathway_id == "member-in-training":
        notes.insert(0, "APEGA's application fee for new members-in-training is not published on the pages "
                        "we use; check it in myAPEGA.")
    if regulator_id == "acp":
        notes = ["Not listed here: University of Alberta DCPP tuition, English tests, liability insurance and "
                 "SPT costs. PEBC doesn't say whether tax applies to its fees; Part I and II amounts are its "
                 "2027 fees."]
    if regulator_id == "cips":
        notes = ["The I.S.P. is voluntary: you can work in computing in Alberta without it. Only APEGA can license "
                 "you to practise as a software engineer.",
                 "Not listed here: the yearly CIPS membership fee (shown on CIPS's membership application) and "
                 "credential assessment fees. CIPS fees are before GST."]
    if regulator_id == "crna":
        notes.insert(0, "Professional liability protection is bought separately from the Canadian Nurses "
                        "Protective Society.")
    return notes


PROFESSIONS = {
    "apega": (ApegaProfile, apega_pathway, lambda req, p, today: apega_status(req, p), apega_fees),
    "crna": (CrnaProfile, crna_pathway, crna_status, crna_fees),
    "acp": (AcpProfile, acp_pathway, acp_status, acp_fees),
    "cips": (CipsProfile, cips_pathway, cips_status, cips_fees),
}


def build(conn, regulator_id: str, profile, today: date | None = None) -> dict:
    today = today or date.today()
    _, choose_pathway, status_of, fees_for = PROFESSIONS[regulator_id]
    regulator = regulatory_repo.regulator(conn, regulator_id)
    pathways = regulatory_repo.pathways(conn, regulator_id)
    pathway_id = choose_pathway(profile)
    # Without enough answers to choose a route, show the requirements of the most common one.
    shown = pathway_id or next(iter(pathways))
    items = []
    for req in regulatory_repo.requirements(conn, regulator_id, shown):
        status, detail = status_of(req, profile, today)
        items.append({"id": req["id"], "title": req["title"], "category": req["category"],
                      "description": req["description"], "status": status, "detail": detail,
                      "stage": (req["details"] or {}).get("stage"), "source_url": req["source_url"]})

    fee_rows = regulatory_repo.fees(conn, regulator_id)
    costs = []
    for fee_id, status, why in fees_for(profile, pathway_id, fee_rows, today):
        fee = fee_rows.get(fee_id)
        if fee:
            costs.append({"name": fee["name"], "amount": fee["amount"], "currency": fee["currency"],
                          "gst": fee["gst"], "payee": fee["payee"], "status": status, "note": why,
                          "source_url": fee["source_url"]})
    totals: dict[str, dict[str, float]] = {}
    for c in costs:
        bucket = "expected" if c["status"] == TO_DO else "possible"
        totals.setdefault(bucket, {}).setdefault(c["currency"], 0.0)
        totals[bucket][c["currency"]] = round(totals[bucket][c["currency"]] + c["amount"], 2)

    order = {TO_DO: 0, TO_CONFIRM: 1}
    next_steps = [f"{i['title']}: {i['detail']}" if i["detail"] else i["title"]
                  for i in sorted(items, key=lambda i: order.get(i["status"], 9)) if i["status"] in order][:6]
    return {
        "regulator": {k: (v.isoformat() if isinstance(v, date) else v) for k, v in regulator.items()},
        "pathway": pathways.get(pathway_id),
        "pathway_note": None if pathway_id else "Answer the questions marked 'to confirm' to choose your route; "
                                                "requirements below are for the most common route.",
        "progress": {s: sum(1 for i in items if i["status"] == s) for s in (DONE, TO_DO, TO_CONFIRM, MAY_APPLY, NOT_NEEDED)},
        "requirements": items,
        "next_steps": next_steps,
        "costs": costs,
        "cost_totals": totals,
        "cost_notes": cost_notes(regulator_id, pathway_id),
        "timelines": regulatory_repo.timelines(conn, regulator_id),
    }
