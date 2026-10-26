"""Input validation and date edge cases found in the UI review."""
from datetime import date, timedelta
import math
import os
import unittest

from pydantic import ValidationError

from models.profiles import CrnaProfile, EnglishResult
from services.roadmap import TO_DO, _english


class EnglishValidationRegressions(unittest.TestCase):
    def result(self, **changes):
        values = {"test": "IELTS Academic", "taken_on": "2025-03-01", "scores": {"writing": 7}}
        return EnglishResult(**(values | changes))

    def test_future_date_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.result(taken_on=date.today() + timedelta(days=1))

    def test_ielts_bounds_and_half_bands(self):
        for value in [-1, 9.5, 12, 6.25, math.inf, math.nan]:
            with self.subTest(value=value), self.assertRaises(ValidationError):
                self.result(scores={"writing": value})
        for value in [0, 6.5, 9]:
            self.assertEqual(self.result(scores={"writing": value}).scores["writing"], value)

    def test_celban_levels_are_whole_and_have_no_overall(self):
        for scores in [{"writing": 7.5}, {"listening": 13}, {"overall": 8}]:
            with self.subTest(scores=scores), self.assertRaises(ValidationError):
                self.result(test="CELBAN", scores=scores)
        self.assertEqual(self.result(test="CELBAN", scores={"listening": 9}).scores["listening"], 9)

    def test_missing_bands_remain_missing_not_inferred(self):
        self.assertNotIn("reading", self.result().scores)

    def test_conflicting_exemption_and_test_are_rejected(self):
        with self.assertRaises(ValidationError):
            CrnaProfile(english=self.result(), english_exemption=True)
        self.assertTrue(CrnaProfile(english_exemption=True).english_exemption)

    def test_leap_day_has_safe_calendar_anniversary(self):
        p = CrnaProfile(english={"test": "IELTS Academic", "taken_on": "2024-02-29", "scores": {"writing": 7}})
        rules = {"tests": [{"name": "IELTS Academic", "valid_years": 2, "min_scores": {"writing": 6.5}}]}
        self.assertEqual(_english(rules, p, date(2026, 2, 28))[0], "done")
        status, detail = _english(rules, p, date(2026, 3, 1))
        self.assertEqual(status, TO_DO)
        self.assertIn("2026-02-28", detail)


@unittest.skipUnless(os.environ.get("DATABASE_URL"), "requires loaded regulator data")
class ApiValidationRegressions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from fastapi.testclient import TestClient
        from main import app
        cls.client = TestClient(app)

    def test_invalid_english_returns_actionable_422(self):
        for english in [
            {"test": "IELTS Academic", "taken_on": "2099-01-01", "scores": {"writing": 7}},
            {"test": "IELTS Academic", "taken_on": "2025-01-01", "scores": {"writing": 12}},
        ]:
            r = self.client.post("/roadmap/crna", json={"english": english})
            self.assertEqual(r.status_code, 422)
            self.assertTrue(r.json()["detail"][0]["msg"])

    def test_leap_day_returns_a_roadmap_not_a_server_error(self):
        r = self.client.post("/roadmap/crna", json={"english": {
            "test": "IELTS Academic", "taken_on": "2024-02-29", "scores": {"writing": 7}}})
        self.assertEqual(r.status_code, 200)
        english = next(i for i in r.json()["requirements"] if i["id"] == "english")
        self.assertEqual(english["status"], "to_do")
