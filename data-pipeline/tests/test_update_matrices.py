"""Loads the matrices into a real PostgreSQL database. Skipped without TEST_DATABASE_URL.

Uses its own schema (dropped afterwards), so it never touches loaded data.
"""
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pydantic import ValidationError  # noqa: E402

from matrix_models import MATRICES_DIR  # noqa: E402
from update_matrices import sync  # noqa: E402

DB_URL = os.environ.get("TEST_DATABASE_URL")


@unittest.skipUnless(DB_URL, "set TEST_DATABASE_URL to run database tests")
class SyncTests(unittest.TestCase):
    def setUp(self):
        import psycopg
        self.conn = psycopg.connect(DB_URL)
        self.conn.execute("DROP SCHEMA IF EXISTS sync_test CASCADE")
        self.conn.execute("CREATE SCHEMA sync_test")
        self.conn.execute("SET search_path TO sync_test")
        self.conn.commit()
        self.dir = Path(tempfile.mkdtemp())
        for p in MATRICES_DIR.glob("*.json"):
            shutil.copy(p, self.dir)

    def tearDown(self):
        self.conn.rollback()
        self.conn.execute("DROP SCHEMA sync_test CASCADE")
        self.conn.commit()
        self.conn.close()
        shutil.rmtree(self.dir)

    def count(self, table, rid):
        return self.conn.execute(f"SELECT count(*) FROM {table} WHERE regulator_id = %s", (rid,)).fetchone()[0]

    def test_loads_everything_with_sources(self):
        self.assertEqual(sync(self.conn, self.dir), {"apega": "loaded", "crna": "loaded"})
        self.assertEqual(self.count("competencies", "apega"), 22)
        self.assertGreater(self.count("requirement_pathways", "crna"), 0)
        fee = self.conn.execute(
            "SELECT f.amount, s.url FROM fees f JOIN sources s ON s.regulator_id = f.regulator_id"
            " AND s.id = f.source_id WHERE f.regulator_id = 'apega' AND f.id = 'application-new'").fetchone()
        self.assertEqual(float(fee[0]), 500.0)
        self.assertTrue(fee[1].startswith("https://www.apega.ca/"))
        english = self.conn.execute(
            "SELECT details->'tests'->1->'min_scores'->>'overall' FROM requirements"
            " WHERE regulator_id = 'crna' AND id = 'english'").fetchone()[0]
        self.assertEqual(english, "7.0")
        self.assertEqual(self.count("competencies", "crna"), 101)
        self.assertEqual(self.count("competency_categories", "apega"), 6)

    def test_second_run_skips_unchanged_and_force_reloads(self):
        sync(self.conn, self.dir)
        self.assertEqual(sync(self.conn, self.dir), {"apega": "unchanged", "crna": "unchanged"})
        self.assertEqual(sync(self.conn, self.dir, force=True), {"apega": "loaded", "crna": "loaded"})
        self.assertEqual(self.count("competencies", "apega"), 22)  # replaced, not duplicated

    def test_changed_matrix_replaces_old_rows(self):
        sync(self.conn, self.dir)
        path = self.dir / "apega_engineering.json"
        data = json.loads(path.read_text())
        data["fees"] = data["fees"][:1]
        data["fees"][0]["amount"] = 550.0
        path.write_text(json.dumps(data))
        self.assertEqual(sync(self.conn, self.dir)["apega"], "loaded")
        rows = self.conn.execute("SELECT amount FROM fees WHERE regulator_id = 'apega'").fetchall()
        self.assertEqual([float(r[0]) for r in rows], [550.0])

    def test_invalid_file_loads_nothing(self):
        path = self.dir / "crna_registered_nurse.json"
        data = json.loads(path.read_text())
        data["fees"][0]["source"] = "unknown"
        path.write_text(json.dumps(data))
        with self.assertRaises(ValidationError):
            sync(self.conn, self.dir)
        self.conn.rollback()
        exists = self.conn.execute("SELECT to_regclass('sync_test.regulators')").fetchone()[0]
        self.assertIsNone(exists)


if __name__ == "__main__":
    unittest.main()
