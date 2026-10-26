import copy
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pydantic import ValidationError  # noqa: E402

from matrix_models import MATRICES_DIR, Matrix, load_all  # noqa: E402


def raw(name):
    return json.loads((MATRICES_DIR / name).read_text(encoding="utf-8"))


class ShippedMatricesTests(unittest.TestCase):
    def test_all_matrices_validate(self):
        ids = {m.regulator.id for m in load_all()}
        self.assertEqual(ids, {"apega", "crna"})

    def test_every_source_is_an_official_regulator_page(self):
        for m in load_all():
            host = m.regulator.website.host.removeprefix("www.")
            for s in m.sources:
                self.assertEqual(s.url.scheme, "https")
                if s.publisher != "regulator":
                    continue
                self.assertTrue(s.url.host.endswith(host), f"{s.url} is not on {host}")

    def test_apega_has_22_competencies_and_8_mandatory(self):
        apega = next(m for m in load_all() if m.regulator.id == "apega")
        self.assertEqual(len(apega.competencies), 22)
        mandatory = sorted(c.code for c in apega.competencies if c.mandatory)
        self.assertEqual(mandatory, ["1.1", "1.6", "1.9", "2.1", "2.2", "2.3", "5.1", "6.2"])

    def test_crna_english_scores_match_published_minimums(self):
        crna = next(m for m in load_all() if m.regulator.id == "crna")
        english = next(r for r in crna.requirements if r.id == "english")
        tests = {t["name"]: t["min_scores"] for t in english.details["tests"]}
        self.assertEqual(tests["IELTS Academic"]["overall"], 7.0)
        self.assertEqual(tests["CELBAN"]["listening"], 9)

    def test_apega_category_minimums(self):
        apega = next(m for m in load_all() if m.regulator.id == "apega")
        mins = {c.name: c.min_average for c in apega.competency_categories}
        self.assertEqual(len(mins), 6)
        self.assertEqual(mins["Technical Competence"], 3.0)
        self.assertEqual(mins["Project and Financial Management"], 2.0)

    def test_crna_has_101_entry_level_competencies_in_9_roles(self):
        crna = next(m for m in load_all() if m.regulator.id == "crna")
        self.assertEqual(len(crna.competencies), 101)
        self.assertEqual(len({c.category for c in crna.competencies}), 9)
        for c in crna.competencies:
            self.assertNotRegex(c.name, r"\b(?!MAID\b)[A-Z]{4,}\b", f"{c.code} still has glossary capitals")

    def test_crna_fees_are_the_current_practice_year(self):
        crna = next(m for m in load_all() if m.regulator.id == "crna")
        permit = next(f for f in crna.fees if f.id == "rn-permit")
        self.assertEqual((permit.amount, permit.period), (483.00, "2026-2027"))

    def test_nclex_fee_change_has_no_gap(self):
        crna = next(m for m in load_all() if m.regulator.id == "crna")
        fees = {f.id: f for f in crna.fees}
        old, new = fees["nclex-registration"], fees["nclex-registration-2027"]
        self.assertEqual((new.effective_from - old.effective_until).days, 1)

    def test_fees_from_third_party_pages_are_not_paid_to_the_regulator(self):
        for m in load_all():
            publishers = {s.id: s.publisher for s in m.sources}
            for f in m.fees:
                if publishers[f.source] != "regulator":
                    self.assertNotEqual(f.payee, m.regulator.short_name, f"{m.regulator.id}/{f.id}")


class ValidationRulesTests(unittest.TestCase):
    def setUp(self):
        self.data = raw("apega_engineering.json")

    def invalid(self, data):
        with self.assertRaises(ValidationError):
            Matrix.model_validate(data)

    def test_rejects_unknown_source(self):
        data = copy.deepcopy(self.data)
        data["fees"][0]["source"] = "made-up-page"
        self.invalid(data)

    def test_rejects_unknown_pathway(self):
        data = copy.deepcopy(self.data)
        data["requirements"][0]["pathways"] = ["nonexistent"]
        self.invalid(data)

    def test_rejects_duplicate_ids(self):
        data = copy.deepcopy(self.data)
        data["fees"].append(copy.deepcopy(data["fees"][0]))
        self.invalid(data)

    def test_rejects_zero_fee(self):
        data = copy.deepcopy(self.data)
        data["fees"][0]["amount"] = 0
        self.invalid(data)

    def test_rejects_mandatory_competency_without_level(self):
        data = copy.deepcopy(self.data)
        del data["competencies"][0]["min_level"]
        self.invalid(data)

    def test_rejects_unexpected_fields(self):
        data = copy.deepcopy(self.data)
        data["fees"][0]["amount_usd"] = 1
        self.invalid(data)

    def test_rejects_fee_ending_before_it_starts(self):
        data = copy.deepcopy(self.data)
        data["fees"][0]["effective_from"] = "2027-01-01"
        data["fees"][0]["effective_until"] = "2026-01-01"
        self.invalid(data)

    def test_rejects_category_minimum_for_unknown_category(self):
        data = copy.deepcopy(self.data)
        data["competency_categories"].append({"name": "Typo", "min_average": 2.0, "source": "apega-scoring"})
        self.invalid(data)

    def test_rejects_source_retrieved_after_verification(self):
        data = copy.deepcopy(self.data)
        data["sources"][0]["retrieved_on"] = "2099-01-01"
        self.invalid(data)


if __name__ == "__main__":
    unittest.main()
