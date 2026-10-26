"""Personal licensing roadmap: route, requirement status, costs and timelines.

Requirements, thresholds (hours, test scores, months) and fees come from the regulator
data in the database; this module only compares them with the applicant's answers.
Unknown answers give "to_confirm", never a guess.

Statuses: done, to_do, to_confirm (we need an answer), may_apply (only if the
regulator asks for it), not_needed.
"""
from __future__ import annotations

from datetime import date

from models.profiles import ApegaProfile, CrnaProfile
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


def _english(details: dict, p: CrnaProfile, today: date) -> tuple[str, str]:
    if p.english_exemption:
        return DONE, "Exemption."
    if p.english is None:
        return (TO_DO, "Take IELTS Academic or CELBAN.") if p.english_exemption is False else (TO_CONFIRM, "")
    test = next((t for t in details.get("tests", []) if t["name"] == p.english.test), None)
    if test is None:
        return TO_DO, f"{p.english.test} is not accepted."
    expires = p.english.taken_on.replace(year=p.english.taken_on.year + test["valid_years"])
    low = [f"{part} {p.english.scores.get(part, 'missing')} (needs {minimum})"
           for part, minimum in test["min_scores"].items() if p.english.scores.get(part, -1) < minimum]
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


# ---------------------------------------------------------------- shared

def cost_notes(regulator_id: str, pathway_id: str | None) -> list[str]:
    notes = ["Third-party costs not listed here: credential evaluation (WES, NNAS or another provider), "
             "English tests, document translation and courier fees."]
    if regulator_id == "apega" and pathway_id == "member-in-training":
        notes.insert(0, "APEGA's application fee for new members-in-training is not published on the pages "
                        "we use; check it in myAPEGA.")
    if regulator_id == "crna":
        notes.insert(0, "Professional liability protection is bought separately from the Canadian Nurses "
                        "Protective Society.")
    return notes


PROFESSIONS = {
    "apega": (ApegaProfile, apega_pathway, lambda req, p, today: apega_status(req, p), apega_fees),
    "crna": (CrnaProfile, crna_pathway, crna_status, crna_fees),
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
                      "source_url": req["source_url"]})

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
