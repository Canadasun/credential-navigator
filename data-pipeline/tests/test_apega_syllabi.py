import copy
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pydantic import ValidationError  # noqa: E402

from crawlers.apega_syllabi import parse_checklist, parse_page, split_choice  # noqa: E402
from matrix_models import SYLLABI_DIR, Syllabus, load_syllabus  # noqa: E402

PAGE = """<nav><h2>Menu</h2></nav><main>
<h1>Mechanical Engineering Syllabi &amp; Exam Descriptions</h1><h1>2016 Edition</h1>
<h2>Group A</h2><p>Compulsory exams – Six required: A1-A5 and <b>one </b>of A6-A7</p>
<h3>16-Mec-A1 Applied Thermodynamics</h3><p>Cycles.</p><p>Heat transfer.</p>
<h3>16-Mec-A2 Machines</h3><p>Kinematics.</p>
<h3>16-Mec-A3 Control</h3><p>Feedback.</p>
<h3>16-Mec-A4 Machine Elements</h3><p>Design.</p>
<h3>16-Mec-A5 Electronics</h3><p>Devices.</p>
<h3>16-Mec-A6 Fluids</h3><p>Flow.</p>
<h3>16-Mec-A7&nbsp; Materials</h3><p>Metals.</p>
<h2>Group B</h2><p>Elective Exams (three required)</p>
<h3>16-Mec-B1 Robotics</h3><p>Arms.</p>
<h3>16-Mec-B2 Vibration</h3><p>Modes.</p>
<h3>16-Mec-B13 Biomechanics (04-Bio-A4)</h3><p>Tissue.</p>
<h2>Apply</h2><p>Register in myAPEGA.</p>
</main>"""

CHECKLIST = """APEGA Mechanical Engineering Assessment Checklist
This form is provided for assessment purposes only (06.02.2020).
Basic Studies &
Compulsory Exams
04-BS-1     Mathematics
04-BS-3     Statics and Dynamics
Optional Exams
(Requires 1)
04-BS-2     Probability and Statistics
04-BS-4     Electric Circuits and Power
Mechanical
Group A (Requires 6)
16-Mec-A1   Applied Thermodynamics
"""


class ParsePageTests(unittest.TestCase):
    def setUp(self):
        self.parsed = parse_page(PAGE)

    def test_edition_groups_and_exams(self):
        self.assertEqual(self.parsed["edition"], "2016 Edition")
        self.assertEqual([(g["name"], g["kind"], g["required"]) for g in self.parsed["groups"]],
                         [("Group A", "compulsory", 6), ("Group B", "elective", 3)])
        self.assertEqual(len(self.parsed["exams"]), 10)

    def test_description_joins_paragraphs_and_menu_is_ignored(self):
        first = self.parsed["exams"][0]
        self.assertEqual((first["code"], first["description"]), ("16-Mec-A1", "Cycles. Heat transfer."))

    def test_non_breaking_space_after_code(self):
        self.assertEqual(self.parsed["exams"][6]["title"], "Materials")

    def test_cross_listed_exam(self):
        bio = self.parsed["exams"][-1]
        self.assertEqual((bio["title"], bio["same_as"]), ("Biomechanics", ["04-Bio-A4"]))

    def test_choice_rule_splits_group(self):
        fixed, choice = split_choice(self.parsed["groups"][0])
        self.assertEqual((fixed["required"], len(fixed["exams"])), (5, 5))
        self.assertEqual((choice["required"], choice["exams"]), (1, ["16-Mec-A6", "16-Mec-A7"]))

    def test_plain_group_is_not_split(self):
        self.assertEqual(len(split_choice(self.parsed["groups"][1])), 1)


class ParseChecklistTests(unittest.TestCase):
    def test_basic_studies(self):
        basic = parse_checklist(CHECKLIST)
        self.assertEqual(basic["compulsory"], ["04-BS-1", "04-BS-3"])
        self.assertEqual(basic["optional"], ["04-BS-2", "04-BS-4"])
        self.assertEqual(basic["optional_required"], 1)
        self.assertEqual(basic["checklist_date"], "2020-06-02")

    def test_missing_section_is_an_error(self):
        with self.assertRaises(ValueError):
            parse_checklist("no basic studies here")


class ShippedSyllabusTests(unittest.TestCase):
    def setUp(self):
        self.path = SYLLABI_DIR / "apega_engineering.json"
        self.syllabus = load_syllabus(self.path)

    def test_covers_14_engineering_disciplines(self):
        self.assertEqual(len(self.syllabus.disciplines), 14)
        self.assertEqual(self.syllabus.preliminary.required, 4)
        self.assertEqual(self.syllabus.complementary.exams, ["98-CS-1", "98-CS-2", "98-CS-3"])

    def test_mechanical_has_the_choice_group(self):
        mech = next(d for d in self.syllabus.disciplines if d.id == "mechanical-engineering")
        self.assertEqual([g.required for g in mech.groups], [5, 1, 3])

    def test_rejects_group_listing_unknown_exam(self):
        data = json.loads(self.path.read_text(encoding="utf-8"))
        bad = copy.deepcopy(data)
        bad["disciplines"][0]["groups"][0]["exams"].append("99-Fake-A1")
        with self.assertRaises(ValidationError):
            Syllabus.model_validate(bad)

    def test_rejects_requirement_larger_than_group(self):
        data = json.loads(self.path.read_text(encoding="utf-8"))
        data["complementary"]["required"] = 4
        with self.assertRaises(ValidationError):
            Syllabus.model_validate(data)


if __name__ == "__main__":
    unittest.main()
