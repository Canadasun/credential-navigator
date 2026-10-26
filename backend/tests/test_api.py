"""End to end through the API against the loaded regulatory data. Needs DATABASE_URL with
data loaded (data-pipeline/update_matrices.py)."""
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
FIXTURES = Path(__file__).parent / "fixtures"


@unittest.skipUnless(os.environ.get("DATABASE_URL"), "set DATABASE_URL to a loaded database")
class AnalysisApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from fastapi.testclient import TestClient
        from main import app
        cls.client = TestClient(app)

    def post(self, name, discipline="mechanical-engineering", content_type="application/pdf"):
        return self.client.post("/apega/analysis", data={"discipline": discipline},
                                files={"file": (name, (FIXTURES / name).read_bytes(), content_type)})

    def test_lists_disciplines(self):
        ids = {d["id"] for d in self.client.get("/apega/disciplines").json()}
        self.assertIn("software-engineering", ids)
        self.assertEqual(len(ids), 14)

    def test_course_descriptions_find_the_missing_complementary_studies(self):
        response = self.post("mechanical_course_descriptions.pdf")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("Advisory only", body["disclaimer"])
        groups = {g["name"]: g for g in body["groups"]}
        self.assertEqual(groups["Group A"]["likely_covered"], 5)
        self.assertEqual(groups["Complementary Studies"]["possibly_needed"], 3)  # no economics, society or management course
        codes = [m["best_course"]["code"] for g in body["groups"] for m in g["exams"] if m["best_course"]]
        self.assertEqual(len(codes), len(set(codes)), "a course was counted twice")

    def test_titles_only_transcript_gets_a_note(self):
        body = self.post("mechanical_transcript.pdf").json()
        self.assertTrue(any("only a title" in note for note in body["notes"]))

    def test_scanned_transcript_is_read_with_ocr(self):
        from services.pdf_text import ocr_available
        if not ocr_available():
            self.skipTest("Tesseract is not installed (run in the Docker image)")
        body = self.post("mechanical_transcript_scanned.pdf").json()
        self.assertEqual(body["document"]["method"], "ocr")
        self.assertEqual(body["summary"]["courses_found"], 6)
        self.assertTrue(any("OCR" in note for note in body["notes"]))

    def test_scanned_pdf_is_422(self):
        response = self.post("scanned_like.pdf")
        self.assertEqual(response.status_code, 422)
        self.assertRegex(response.json()["detail"], "scanned|OCR")

    def test_unknown_discipline_is_404(self):
        self.assertEqual(self.post("mechanical_transcript.pdf", discipline="astrology").status_code, 404)


if __name__ == "__main__":
    unittest.main()
