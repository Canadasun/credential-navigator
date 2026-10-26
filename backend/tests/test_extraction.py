import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from services.course_extraction import extract_courses  # noqa: E402
from services.pdf_text import UnreadableDocument, extract_text  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures"


class PdfTextTests(unittest.TestCase):
    def test_reads_text_pdf(self):
        self.assertIn("Calculus I", extract_text((FIXTURES / "mechanical_transcript.pdf").read_bytes()))

    def test_scanned_pdf_is_rejected_with_reason(self):
        with self.assertRaisesRegex(UnreadableDocument, "scanned"):
            extract_text((FIXTURES / "scanned_like.pdf").read_bytes())

    def test_non_pdf_is_rejected(self):
        with self.assertRaisesRegex(UnreadableDocument, "not a PDF"):
            extract_text(b"MATH 101 Calculus I")

    def test_corrupt_pdf_is_rejected(self):
        with self.assertRaises(UnreadableDocument):
            extract_text(b"%PDF-1.7 this is not really a pdf")


class CourseExtractionTests(unittest.TestCase):
    def test_transcript_lines(self):
        courses = extract_courses("Semester 1\nMATH 101 Calculus I 4 A\nMATH-201 Linear Algebra 4 A-\n"
                                  "MECH210 Statics and Dynamics 4 B+\nCumulative GPA 3.6\n")
        self.assertEqual([(c.code, c.title, c.credits, c.grade) for c in courses],
                         [("MATH 101", "Calculus I", 4.0, "A"), ("MATH 201", "Linear Algebra", 4.0, "A-"),
                          ("MECH 210", "Statics and Dynamics", 4.0, "B+")])

    def test_descriptions_follow_their_course(self):
        courses = extract_courses("Program overview text\nCHEM 105 Engineering Chemistry 3\n"
                                  "Stoichiometry and equilibrium.\nKinetics.\nPage 2\nCS 110 Programming\nC and Matlab.\n")
        self.assertEqual([c.description for c in courses], ["Stoichiometry and equilibrium. Kinetics.", "C and Matlab."])

    def test_repeated_course_keeps_one_entry(self):
        courses = extract_courses("MATH 101 Calculus I 4 F\nMATH 101 Calculus I 4 B\nLimits and derivatives.\n")
        self.assertEqual(len(courses), 1)
        self.assertEqual(courses[0].description, "Limits and derivatives.")

    def test_fixture_documents(self):
        transcript = extract_courses(extract_text((FIXTURES / "mechanical_transcript.pdf").read_bytes()))
        descriptions = extract_courses(extract_text((FIXTURES / "mechanical_course_descriptions.pdf").read_bytes()))
        self.assertEqual(len(transcript), 6)
        self.assertEqual(len(descriptions), 21)
        self.assertTrue(all(len(c.description) > 30 for c in descriptions))


if __name__ == "__main__":
    unittest.main()
