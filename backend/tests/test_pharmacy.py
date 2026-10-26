"""Alberta College of Pharmacy (ACP) roadmap: route, English (IELTS and OET), PEBC, DCPP and SPT."""
import os
import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pydantic import ValidationError  # noqa: E402

from models.profiles import AcpProfile  # noqa: E402
from services.roadmap import (DONE, NOT_NEEDED, TO_CONFIRM, TO_DO, _english, acp_fees,  # noqa: E402
                              acp_pathway, acp_status)

ENGLISH = {"tests": [
    {"name": "IELTS Academic", "valid_years": 2,
     "min_scores": {"reading": 7.0, "listening": 7.0, "speaking": 7.0, "writing": 6.5}},
    {"name": "OET", "valid_years": 2,
     "min_scores": {"reading": "B", "listening": "B", "speaking": "B", "writing": "C+"}}]}
TODAY = date(2026, 10, 25)


def req(rid, **details):
    return {"id": rid, "category": "exam", "details": details}


def oet(**scores):
    base = {"reading": "B", "listening": "A", "speaking": "B", "writing": "C+"}
    return AcpProfile(english={"test": "OET", "taken_on": "2026-01-10", "scores": base | scores})


class AcpRouteTests(unittest.TestCase):
    def test_routes(self):
        self.assertEqual(acp_pathway(AcpProfile(us_acpe_pharmd=False)), "international")
        self.assertEqual(acp_pathway(AcpProfile(us_acpe_pharmd=True)), "us-pharmd")
        self.assertIsNone(acp_pathway(AcpProfile()))


class AcpEnglishTests(unittest.TestCase):
    def test_oet_minimums_met(self):
        self.assertEqual(_english(ENGLISH, oet(), TODAY)[0], DONE)

    def test_oet_grade_below_minimum_is_named(self):
        status, detail = _english(ENGLISH, oet(writing="C"), TODAY)
        self.assertEqual(status, TO_DO)
        self.assertIn("writing C (needs C+)", detail)

    def test_ielts_writing_6_5_is_enough_but_reading_6_5_is_not(self):
        p = AcpProfile(english={"test": "IELTS Academic", "taken_on": "2026-01-10",
                                "scores": {"reading": 6.5, "listening": 7, "speaking": 7, "writing": 6.5}})
        status, detail = _english(ENGLISH, p, TODAY)
        self.assertEqual(status, TO_DO)
        self.assertIn("reading 6.5 (needs 7.0)", detail)
        self.assertNotIn("writing", detail)

    def test_missing_band_is_not_met(self):
        p = AcpProfile(english={"test": "OET", "taken_on": "2026-01-10", "scores": {"reading": "A"}})
        self.assertIn("writing missing", _english(ENGLISH, p, TODAY)[1])

    def test_no_test_and_no_exemption_names_the_accepted_tests(self):
        self.assertIn("IELTS Academic or OET", _english(ENGLISH, AcpProfile(english_exemption=False), TODAY)[1])

    def test_invalid_results_are_rejected(self):
        for english in [{"test": "OET", "taken_on": "2026-01-10", "scores": {"writing": 350}},
                        {"test": "OET", "taken_on": "2026-01-10", "scores": {"writing": "B+"}},
                        {"test": "IELTS Academic", "taken_on": "2026-01-10", "scores": {"writing": "B"}},
                        {"test": "IELTS Academic", "taken_on": "2026-01-10", "scores": {"overall": 7}},
                        {"test": "CELBAN", "taken_on": "2026-01-10", "scores": {"writing": 8}}]:
            with self.subTest(english=english), self.assertRaises(ValidationError):
                AcpProfile(english=english)

    def test_us_pharmd_usually_needs_no_test(self):
        self.assertEqual(acp_status(req("english", **ENGLISH), AcpProfile(us_acpe_pharmd=True), TODAY)[0], NOT_NEEDED)


class AcpStatusTests(unittest.TestCase):
    def test_one_pebc_part_or_dcpp_opens_the_provisional_register(self):
        rule = req("provisional-exam")
        self.assertEqual(acp_status(rule, AcpProfile(pebc_part1_passed=True), TODAY)[0], DONE)
        self.assertEqual(acp_status(rule, AcpProfile(dcpp_completed=True), TODAY)[0], DONE)
        self.assertEqual(acp_status(rule, AcpProfile(), TODAY)[0], TO_CONFIRM)
        self.assertEqual(acp_status(rule, AcpProfile(pebc_part1_passed=False, pebc_part2_passed=False,
                                                     dcpp_completed=False), TODAY)[0], TO_DO)

    def test_qualifying_exam_names_the_missing_part(self):
        status, detail = acp_status(req("pebc-qualifying"), AcpProfile(pebc_part1_passed=True,
                                                                       pebc_part2_passed=False), TODAY)
        self.assertEqual(status, TO_DO)
        self.assertIn("Part II (OSCE)", detail)
        self.assertNotIn("Part I (MCQ)", detail)

    def test_dcpp_exemption_after_first_attempt_passes(self):
        p = AcpProfile(pebc_part1_passed=True, pebc_part2_passed=True, pebc_both_first_attempt=True)
        self.assertEqual(acp_status(req("dcpp"), p, TODAY)[0], NOT_NEEDED)
        self.assertEqual(acp_status(req("dcpp"), AcpProfile(dcpp_completed=False), TODAY)[0], TO_DO)

    def test_first_attempt_claim_needs_both_parts_passed(self):
        with self.assertRaises(ValidationError):
            AcpProfile(pebc_part1_passed=True, pebc_both_first_attempt=True)

    def test_spt_counts_experiences_from_the_data(self):
        rule = req("spt", min_experiences=2, min_hours_each=320)
        status, detail = acp_status(rule, AcpProfile(spt_experiences_completed=1), TODAY)
        self.assertEqual(status, TO_DO)
        self.assertIn("1 more practical experience of at least 320 hours", detail)
        self.assertIn("provisional register", detail)
        self.assertEqual(acp_status(rule, AcpProfile(spt_experiences_completed=2), TODAY)[0], DONE)

    def test_fees_follow_progress(self):
        ids = [f for f, _, _ in acp_fees(AcpProfile(gateway_enrolled=True, pebc_part1_passed=True),
                                         "us-pharmd", {}, TODAY)]
        self.assertNotIn("gateway-enrolment", ids)
        self.assertNotIn("pebc-part1", ids)
        self.assertIn("pebc-us-document-evaluation", ids)
        self.assertIn("pebc-part2", ids)


@unittest.skipUnless(os.environ.get("DATABASE_URL"), "set DATABASE_URL to a loaded database")
class AcpApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from fastapi.testclient import TestClient
        from main import app
        cls.client = TestClient(app)

    def test_new_international_pharmacist(self):
        body = self.client.post("/roadmap/acp", json={
            "us_acpe_pharmd": False, "gateway_enrolled": False, "document_evaluation_done": False,
            "english": {"test": "OET", "taken_on": "2026-01-10",
                        "scores": {"reading": "B", "listening": "B", "speaking": "B", "writing": "C"}}}).json()
        self.assertEqual(body["pathway"]["id"], "international")
        status = {r["id"]: r["status"] for r in body["requirements"]}
        self.assertEqual((status["gateway"], status["english"], status["dcpp"]), (TO_DO, TO_DO, TO_CONFIRM))
        stages = {r["id"]: r["stage"] for r in body["requirements"]}
        self.assertEqual((stages["gateway"], stages["spt"]), ("provisional", "clinical"))
        # Gateway 390 + Document Evaluation 715 + Part I 870 + Part II 1,950 + registration 703.50 + permit 1,055.25
        self.assertEqual(body["cost_totals"]["expected"], {"CAD": 5683.75})
        self.assertIn("ACP", body["disclaimer"])

    def test_us_pharmd_has_no_dcpp(self):
        body = self.client.post("/roadmap/acp", json={"us_acpe_pharmd": True}).json()
        self.assertNotIn("dcpp", {r["id"] for r in body["requirements"]})

    def test_empty_profile_shows_the_international_route(self):
        body = self.client.post("/roadmap/acp", json={}).json()
        self.assertIsNone(body["pathway"])
        self.assertIn("dcpp", {r["id"] for r in body["requirements"]})


if __name__ == "__main__":
    unittest.main()
