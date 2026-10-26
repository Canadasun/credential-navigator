"""Personal licensing roadmap from an applicant's answers. Answers are not stored."""
from __future__ import annotations

from fastapi import APIRouter

from core.config import connection
from models.profiles import AcpProfile, ApegaProfile, CipsProfile, CrnaProfile
from services import roadmap

router = APIRouter(prefix="/roadmap", tags=["Roadmap"])

ADVISORY = ("Advisory only. This roadmap helps you prepare; {regulator} alone decides on registration. "
            "Fees and requirements were taken from {regulator}'s website on {verified_on}; check the linked "
            "pages before you pay or apply.")
VOLUNTARY = ("Advisory only. The I.S.P. is a voluntary designation; {regulator} alone decides on certification. "
             "Fees and requirements were taken from {regulator}'s website on {verified_on}; check the linked pages "
             "before you pay or apply.")


def respond(regulator_id: str, profile) -> dict:
    with connection() as conn:
        result = roadmap.build(conn, regulator_id, profile)
    result["disclaimer"] = (VOLUNTARY if regulator_id == "cips" else ADVISORY).format(regulator=result["regulator"]["short_name"],
                                           verified_on=result["regulator"]["verified_on"])
    return result


@router.post("/apega")
def apega_roadmap(profile: ApegaProfile) -> dict:
    return respond("apega", profile)


@router.post("/crna")
def crna_roadmap(profile: CrnaProfile) -> dict:
    return respond("crna", profile)


@router.post("/acp")
def acp_roadmap(profile: AcpProfile) -> dict:
    return respond("acp", profile)


@router.post("/cips")
def cips_roadmap(profile: CipsProfile) -> dict:
    return respond("cips", profile)
