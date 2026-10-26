"""Personal licensing roadmap from an applicant's answers. Answers are not stored."""
from __future__ import annotations

from fastapi import APIRouter

from core.config import connection
from models.profiles import ApegaProfile, CrnaProfile
from services import roadmap

router = APIRouter(prefix="/roadmap", tags=["Roadmap"])

ADVISORY = ("Advisory only. This roadmap helps you prepare; {regulator} alone decides on registration. "
            "Fees and requirements were taken from {regulator}'s website on {verified_on}; check the linked "
            "pages before you pay or apply.")


def respond(regulator_id: str, profile) -> dict:
    with connection() as conn:
        result = roadmap.build(conn, regulator_id, profile)
    result["disclaimer"] = ADVISORY.format(regulator=result["regulator"]["short_name"],
                                           verified_on=result["regulator"]["verified_on"])
    return result


@router.post("/apega")
def apega_roadmap(profile: ApegaProfile) -> dict:
    return respond("apega", profile)


@router.post("/crna")
def crna_roadmap(profile: CrnaProfile) -> dict:
    return respond("crna", profile)
