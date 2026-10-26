"""CIPS I.S.P. roadmap for computer science and IT graduates (a voluntary designation)."""
import os
import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pydantic import ValidationError  # noqa: E402

from models.profiles import CipsProfile  # noqa: E402
from services.roadmap import DONE, MAY_APPLY, TO_CONFIRM, TO_DO, cips_fees, cips_pathway, cips_status  # noqa: E402

TODAY = date(2026, 10, 25)
EXPERIENCE = {"id": "experience", "category": "experience", "details": {
    "experience_only_years": 8,
    "years_by_education": {"non-accredited-4-year-university-cs": 4, "accredited-4-year-university-cs": 2}}}


class CipsTests(unittest.TestCase):
    def test_routes(self):
        self.assertEqual(cips_pathway(CipsProfile(education="non-it-or-none")), "experience-only")
        self.assertEqual(cips_pathway(CipsProfile(education="non-accredited-4-year-university-cs")), "education")
        self.assertIsNone(cips_pathway(CipsProfile()))

    def test_years_needed_depend_on_education(self):
        p = CipsProfile(education="non-accredited-4-year-university-cs", it_experience_years=2.5, sfia_level_3=True)
        status, detail = cips_status(EXPERIENCE, p, TODAY)
        self.assertEqual(status, TO_DO)
        self.assertIn("1.5 more years", detail)
        p = CipsProfile(education="accredited-4-year-university-cs", it_experience_years=2.5, sfia_level_3=True)
        self.assertEqual(cips_status(EXPERIENCE, p, TODAY)[0], DONE)

    def test_experience_only_needs_eight_years(self):
        p = CipsProfile(education="non-it-or-none", it_experience_years=6)
        self.assertIn("2 more years", cips_status(EXPERIENCE, p, TODAY)[1])

    def test_enough_years_but_unknown_sfia_level_asks(self):
        p = CipsProfile(education="non-accredited-4-year-university-cs", it_experience_years=5)
        self.assertEqual(cips_status(EXPERIENCE, p, TODAY)[0], TO_CONFIRM)

    def test_recent_hours(self):
        rule = {"id": "recent-hours", "category": "experience", "details": {"hours": 1000}}
        self.assertEqual(cips_status(rule, CipsProfile(hours_last_12_months=1200), TODAY)[0], DONE)
        self.assertIn("400 more hours", cips_status(rule, CipsProfile(hours_last_12_months=600), TODAY)[1])

    def test_recent_graduate_fee_replaces_the_standard_fee(self):
        ids = {f: s for f, s, _ in cips_fees(CipsProfile(recent_graduate=True), "education", {}, TODAY)}
        self.assertNotIn("review-fee", ids)
        unknown = {f: s for f, s, _ in cips_fees(CipsProfile(), None, {}, TODAY)}
        self.assertEqual((unknown["review-fee"], unknown["review-fee-recent-graduate"]), (TO_DO, MAY_APPLY))

    def test_unknown_education_is_rejected(self):
        with self.assertRaises(ValidationError):
            CipsProfile(education="bootcamp")


@unittest.skipUnless(os.environ.get("DATABASE_URL"), "set DATABASE_URL to a loaded database")
class CipsApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from fastapi.testclient import TestClient
        from main import app
        cls.client = TestClient(app)

    def test_foreign_cs_graduate(self):
        body = self.client.post("/roadmap/cips", json={
            "education": "non-accredited-4-year-university-cs", "it_experience_years": 3,
            "hours_last_12_months": 1500, "cips_member": False}).json()
        self.assertEqual(body["pathway"]["id"], "education")
        status = {r["id"]: r["status"] for r in body["requirements"]}
        self.assertEqual((status["experience"], status["recent-hours"], status["membership"]), (TO_DO, DONE, TO_DO))
        self.assertEqual(body["cost_totals"]["expected"], {"CAD": 623.0})  # review 275 + certified member 348
        self.assertIn("voluntary", body["disclaimer"])
        self.assertTrue(any("APEGA" in n for n in body["cost_notes"]))


if __name__ == "__main__":
    unittest.main()
