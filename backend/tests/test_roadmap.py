import os
import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from models.profiles import ApegaProfile, CrnaProfile  # noqa: E402
from services.roadmap import (DONE, TO_CONFIRM, TO_DO, _currency, _effective, _english,  # noqa: E402
                              apega_pathway, apega_status, crna_pathway)

CURRENCY = {"any_of": [
    {"type": "practice_hours", "hours": 450, "within_practice_years": 2},
    {"type": "practice_hours", "hours": 1125, "within_practice_years": 5},
    {"type": "program", "program": "Bridging", "within_practice_years": 5}]}
ENGLISH = {"tests": [{"name": "IELTS Academic", "valid_years": 2, "min_scores": {
    "listening": 7.0, "writing": 6.5, "reading": 6.5, "speaking": 7.0, "overall": 7.0}}]}
TODAY = date(2026, 10, 25)


def ielts(taken_on, **scores):
    base = {"listening": 7.5, "writing": 7.0, "reading": 7.0, "speaking": 7.0, "overall": 7.0}
    return CrnaProfile(english={"test": "IELTS Academic", "taken_on": taken_on, "scores": base | scores})


class PathwayTests(unittest.TestCase):
    def test_apega_routes(self):
        self.assertEqual(apega_pathway(ApegaProfile(experience_months=12)), "member-in-training")
        self.assertEqual(apega_pathway(ApegaProfile(experience_months=60, canadian_citizen_or_pr=True)), "professional-member")
        self.assertEqual(apega_pathway(ApegaProfile(experience_months=60, canadian_citizen_or_pr=False)), "licensee")
        self.assertIsNone(apega_pathway(ApegaProfile(experience_months=60)))
        self.assertIsNone(apega_pathway(ApegaProfile()))

    def test_crna_routes(self):
        self.assertEqual(crna_pathway(CrnaProfile(nclex_passed=True)), "nclex-passed")
        self.assertEqual(crna_pathway(CrnaProfile(nclex_passed=False)), "credential-recognition")
        self.assertIsNone(crna_pathway(CrnaProfile()))

    def test_experience_threshold_comes_from_the_data(self):
        req = {"id": "experience", "details": {"months": 48}, "category": "experience"}
        self.assertEqual(apega_status(req, ApegaProfile(experience_months=40))[0], TO_DO)
        self.assertIn("8 more months", apega_status(req, ApegaProfile(experience_months=40))[1])
        self.assertEqual(apega_status(dict(req, details={"months": 36}), ApegaProfile(experience_months=40))[0], DONE)


class CurrencyTests(unittest.TestCase):
    def test_either_hours_option_is_enough(self):
        self.assertEqual(_currency(CURRENCY, CrnaProfile(practice_hours_last_2_years=450))[0], DONE)
        self.assertEqual(_currency(CURRENCY, CrnaProfile(practice_hours_last_2_years=0,
                                                         practice_hours_last_5_years=1125))[0], DONE)

    def test_program_is_enough(self):
        self.assertEqual(_currency(CURRENCY, CrnaProfile(qualifying_program_last_5_years=True))[0], DONE)

    def test_shortfall_is_explained(self):
        status, detail = _currency(CURRENCY, CrnaProfile(practice_hours_last_2_years=400, practice_hours_last_5_years=900,
                                                         qualifying_program_last_5_years=False))
        self.assertEqual(status, TO_DO)
        self.assertIn("50 more hours within 2 years", detail)
        self.assertIn("225 more hours within 5 years", detail)

    def test_unknown_hours_ask_instead_of_guessing(self):
        self.assertEqual(_currency(CURRENCY, CrnaProfile(practice_hours_last_2_years=10))[0], TO_CONFIRM)


class EnglishTests(unittest.TestCase):
    def test_meets_minimums(self):
        status, detail = _english(ENGLISH, ielts(date(2025, 6, 1)), TODAY)
        self.assertEqual(status, DONE)
        self.assertIn("2027-06-01", detail)

    def test_one_low_band_fails_and_is_named(self):
        status, detail = _english(ENGLISH, ielts(date(2025, 6, 1), writing=6.0), TODAY)
        self.assertEqual(status, TO_DO)
        self.assertIn("writing 6.0 (needs 6.5)", detail)

    def test_expired_scores(self):
        status, detail = _english(ENGLISH, ielts(date(2024, 1, 10)), TODAY)
        self.assertEqual(status, TO_DO)
        self.assertIn("expired", detail)

    def test_exemption(self):
        self.assertEqual(_english(ENGLISH, CrnaProfile(english_exemption=True), TODAY)[0], DONE)


class FeeDateTests(unittest.TestCase):
    FEES = {"old": {"effective_from": None, "effective_until": date(2027, 1, 31)},
            "new": {"effective_from": date(2027, 2, 1), "effective_until": None}}

    def test_picks_the_fee_in_effect(self):
        self.assertEqual(_effective(self.FEES, ["old", "new"], date(2027, 1, 31)), "old")
        self.assertEqual(_effective(self.FEES, ["old", "new"], date(2027, 2, 1)), "new")


@unittest.skipUnless(os.environ.get("DATABASE_URL"), "set DATABASE_URL to a loaded database")
class RoadmapApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from fastapi.testclient import TestClient
        from main import app
        cls.client = TestClient(app)

    def test_nurse_with_low_writing_band(self):
        body = self.client.post("/roadmap/crna", json={
            "nclex_passed": False, "credential_report": "nnas", "nnas_rating": "comparable",
            "practice_hours_last_2_years": 500,
            "english": {"test": "IELTS Academic", "taken_on": "2026-03-01",
                        "scores": {"listening": 8, "writing": 6.0, "reading": 7, "speaking": 7, "overall": 7}}}).json()
        self.assertEqual(body["pathway"]["id"], "credential-recognition")
        status = {r["id"]: r["status"] for r in body["requirements"]}
        self.assertEqual((status["currency-of-practice"], status["english"], status["nclex-rn"]), (DONE, TO_DO, TO_DO))
        self.assertTrue(body["next_steps"][0].startswith(("Pathways", "NCLEX", "English")))
        self.assertIn("CAD", body["cost_totals"]["expected"])
        self.assertIn("Advisory only", body["disclaimer"])
        self.assertTrue(all(r["source_url"].startswith("https://") for r in body["requirements"]))

    def test_engineer_without_accredited_degree(self):
        body = self.client.post("/roadmap/apega", json={
            "experience_months": 72, "canadian_citizen_or_pr": False, "ceab_accredited_degree": False}).json()
        self.assertEqual(body["pathway"]["id"], "licensee")
        status = {r["id"]: r["status"] for r in body["requirements"]}
        self.assertEqual(status["assigned-exams"], "may_apply")
        self.assertNotIn("citizenship", status)  # licensees don't need it
        self.assertEqual(body["cost_totals"]["expected"], {"CAD": 750.0})  # $500 application + $250 NPPE

    def test_empty_profile_asks_questions(self):
        body = self.client.post("/roadmap/apega", json={}).json()
        self.assertIsNone(body["pathway"])
        self.assertIn("to confirm", body["pathway_note"])

    def test_unknown_field_is_rejected(self):
        self.assertEqual(self.client.post("/roadmap/crna", json={"favourite_colour": "blue"}).status_code, 422)


if __name__ == "__main__":
    unittest.main()
