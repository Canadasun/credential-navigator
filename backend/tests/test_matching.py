import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from services.matching import Exam, evaluate_groups, match_exams, tokens  # noqa: E402

CORPUS = [
    Exam("T-1", "Thermodynamics", "First and second laws of thermodynamics, entropy, power cycles, refrigeration."),
    Exam("F-1", "Fluid Mechanics", "Fluid statics, Bernoulli equation, viscous flow in pipes, boundary layers."),
    Exam("E-1", "Engineering Economics", "Time value of money, present worth, rate of return, depreciation."),
    Exam("H-1", "Heat Transfer", "Conduction, convection and radiation heat transfer, heat exchangers.", priority=1),
]


def course(code, title, description=""):
    return {"code": code, "title": title, "description": description}


class MatchingTests(unittest.TestCase):
    def test_tokens_drop_stopwords_and_plurals(self):
        self.assertEqual(tokens("Introduction to the Laws of Thermodynamics and Engineering Cycles"),
                         ["law", "thermodynamic", "cycle"])

    def test_related_course_matches_and_unrelated_exam_is_a_gap(self):
        result = match_exams([course("ME 240", "Thermodynamics", "Laws of thermodynamics, entropy and power cycles.")],
                             CORPUS[:3], CORPUS)
        self.assertEqual(result["T-1"]["status"], "likely_covered")
        self.assertIn("entropy", result["T-1"]["shared_terms"])
        self.assertEqual(result["E-1"]["status"], "possible_gap")
        self.assertIsNone(result["E-1"]["best_course"])

    def test_each_course_counts_once_and_compulsory_exams_come_first(self):
        both = course("ME 300", "Thermal Fluids", "Thermodynamics laws, entropy, convection heat transfer, heat exchangers.")
        result = match_exams([both], CORPUS, CORPUS)
        used = [code for code, r in result.items() if r["best_course"]]
        self.assertEqual(used, ["T-1"])  # H-1 scores well too, but it is a lower-priority exam
        self.assertIsNone(result["H-1"]["best_course"])

    def test_elective_group_counts_only_the_best_n(self):
        matches = {c.code: {"exam": {"code": c.code}, "score": s, "status": st}
                   for c, s, st in [(CORPUS[0], 0.6, "likely_covered"), (CORPUS[1], 0.5, "likely_covered"),
                                    (CORPUS[2], 0.0, "possible_gap")]}
        [group] = evaluate_groups([{"name": "B", "kind": "elective", "required": 2,
                                    "exams": ["T-1", "F-1", "E-1"]}], matches)
        self.assertEqual((group["likely_covered"], group["possibly_needed"], len(group["exams"])), (2, 0, 2))


if __name__ == "__main__":
    unittest.main()
