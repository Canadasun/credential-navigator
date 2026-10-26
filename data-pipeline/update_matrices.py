"""Validate the regulator matrices and sync them into PostgreSQL.

    python update_matrices.py --check      validate the JSON only (no database)
    python update_matrices.py              validate, then load changed matrices into $DATABASE_URL
    python update_matrices.py --force      reload every matrix even if unchanged

A matrix is loaded in one transaction: its regulator's rows are replaced as a whole, so
the database never holds half of one version and half of another. Unchanged matrices
(same content hash as the last load) are skipped.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import sys
from pathlib import Path

from psycopg.types.json import Jsonb

from matrix_models import MATRICES_DIR, SYLLABI_DIR, Matrix, Syllabus, load_matrix, load_syllabus

SCHEMA = Path(__file__).parent / "schema.sql"


def content_hash(*paths: Path) -> str:
    digest = hashlib.sha256()
    for path in paths:
        digest.update(path.read_bytes())
    return digest.hexdigest()


def apply_schema(conn) -> None:
    conn.execute(SCHEMA.read_text(encoding="utf-8"))


def last_loaded_hash(conn, regulator_id: str) -> str | None:
    row = conn.execute(
        "SELECT content_hash FROM matrix_versions WHERE regulator_id = %s ORDER BY id DESC LIMIT 1",
        (regulator_id,)).fetchone()
    return row[0] if row else None


def load(conn, matrix: Matrix, digest: str, syllabus: Syllabus | None = None) -> None:
    r = matrix.regulator
    rid = r.id
    conn.execute("DELETE FROM regulators WHERE id = %s", (rid,))
    conn.execute(
        "INSERT INTO regulators (id, name, short_name, profession, designation, website, verified_on, open_questions)"
        " VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
        (rid, r.name, r.short_name, r.profession, r.designation, str(r.website),
         matrix.verified_on, matrix.open_questions))
    with conn.cursor() as cur:
        cur.executemany(
            "INSERT INTO sources (regulator_id, id, title, url, retrieved_on, publisher) VALUES (%s, %s, %s, %s, %s, %s)",
            [(rid, s.id, s.title, str(s.url), s.retrieved_on, s.publisher) for s in matrix.sources])
        cur.executemany(
            "INSERT INTO pathways (regulator_id, id, name, summary, source_id) VALUES (%s, %s, %s, %s, %s)",
            [(rid, p.id, p.name, p.summary, p.source) for p in matrix.pathways])
        cur.executemany(
            "INSERT INTO requirements (regulator_id, id, category, title, description, conditional, details, source_id)"
            " VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            [(rid, q.id, q.category, q.title, q.description, q.conditional,
              Jsonb(q.details) if q.details is not None else None, q.source) for q in matrix.requirements])
        cur.executemany(
            "INSERT INTO requirement_pathways (regulator_id, requirement_id, pathway_id) VALUES (%s, %s, %s)",
            [(rid, q.id, p) for q in matrix.requirements for p in q.pathways])
        cur.executemany(
            "INSERT INTO documents (regulator_id, id, name, description, submitted_by, conditional, source_id)"
            " VALUES (%s, %s, %s, %s, %s, %s, %s)",
            [(rid, d.id, d.name, d.description, d.submitted_by, d.conditional, d.source) for d in matrix.documents])
        cur.executemany(
            "INSERT INTO fees (regulator_id, id, name, amount, currency, gst, refundable, payee, conditional,"
            " period, effective_from, effective_until, source_id)"
            " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            [(rid, f.id, f.name, f.amount, f.currency, f.gst, f.refundable, f.payee, f.conditional,
              f.period, f.effective_from, f.effective_until, f.source) for f in matrix.fees])
        cur.executemany(
            "INSERT INTO timelines (regulator_id, id, name, max_days, business_days, description, source_id)"
            " VALUES (%s, %s, %s, %s, %s, %s, %s)",
            [(rid, t.id, t.name, t.max_days, t.business_days, t.description, t.source) for t in matrix.timelines])
        cur.executemany(
            "INSERT INTO competencies (regulator_id, code, category, name, min_level, mandatory, source_id)"
            " VALUES (%s, %s, %s, %s, %s, %s, %s)",
            [(rid, c.code, c.category, c.name, c.min_level, c.mandatory, matrix.competency_source)
             for c in matrix.competencies])
        cur.executemany(
            "INSERT INTO competency_categories (regulator_id, name, min_average, source_id) VALUES (%s, %s, %s, %s)",
            [(rid, c.name, c.min_average, c.source) for c in matrix.competency_categories])
    if syllabus:
        load_syllabus_rows(conn, rid, syllabus)
    conn.execute(
        "INSERT INTO matrix_versions (regulator_id, content_hash, verified_on) VALUES (%s, %s, %s)",
        (rid, digest, matrix.verified_on))


def load_syllabus_rows(conn, rid: str, syllabus: Syllabus) -> None:
    with conn.cursor() as cur:
        cur.executemany(
            "INSERT INTO sources (regulator_id, id, title, url, retrieved_on, publisher) VALUES (%s, %s, %s, %s, %s, %s)",
            [(rid, s.id, s.title, str(s.url), s.retrieved_on, s.publisher) for s in syllabus.sources])
        cur.executemany(
            "INSERT INTO syllabus_exams (regulator_id, code, title, description, same_as, source_id)"
            " VALUES (%s, %s, %s, %s, %s, %s)",
            [(rid, e.code, e.title, e.description, e.same_as, e.source) for e in syllabus.exams])
        cur.executemany(
            "INSERT INTO syllabus_disciplines (regulator_id, id, name, edition, basic_compulsory, basic_optional,"
            " basic_optional_required, basic_source_id, source_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
            [(rid, d.id, d.name, d.edition, d.basic_studies.compulsory, d.basic_studies.optional,
              d.basic_studies.optional_required, d.basic_studies.source, d.source) for d in syllabus.disciplines])
        groups = [(None, g, g.source) for g in (syllabus.preliminary, syllabus.complementary)] \
            + [(d.id, g, d.source) for d in syllabus.disciplines for g in d.groups]
        cur.executemany(
            "INSERT INTO syllabus_groups (regulator_id, discipline_id, name, kind, required, rule, exams, source_id)"
            " VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            [(rid, discipline, g.name, g.kind, g.required, g.rule, g.exams, source) for discipline, g, source in groups])


def read_bundles(directory: Path, syllabi_dir: Path) -> list[tuple[Matrix, Syllabus | None, str]]:
    """Validate every matrix and syllabus; pair each syllabus with its regulator's matrix."""
    syllabi = {}
    for path in sorted(syllabi_dir.glob("*.json")) if syllabi_dir.exists() else []:
        syllabus = load_syllabus(path)
        if syllabus.regulator_id in syllabi:
            raise ValueError(f"two syllabi for {syllabus.regulator_id}")
        syllabi[syllabus.regulator_id] = (syllabus, path)
    bundles = []
    for path in sorted(directory.glob("*.json")):
        matrix = load_matrix(path)
        syllabus, syllabus_path = syllabi.pop(matrix.regulator.id, (None, None))
        if syllabus:
            clash = {s.id for s in matrix.sources} & {s.id for s in syllabus.sources}
            if clash:
                raise ValueError(f"syllabus source ids clash with the matrix: {sorted(clash)}")
        bundles.append((matrix, syllabus, content_hash(path, *([syllabus_path] if syllabus_path else []))))
    if syllabi:
        raise ValueError(f"syllabi without a matrix: {sorted(syllabi)}")
    ids = [m.regulator.id for m, _, _ in bundles]
    if len(ids) != len(set(ids)):
        raise ValueError(f"two matrices share a regulator id: {ids}")
    return bundles


def sync(conn, directory: Path = MATRICES_DIR, force: bool = False, syllabi_dir: Path = SYLLABI_DIR) -> dict[str, str]:
    """Load every changed matrix (with its syllabus). Returns {regulator_id: "loaded" | "unchanged"}."""
    # Validate everything first, so one bad file loads nothing at all.
    bundles = read_bundles(directory, syllabi_dir)

    apply_schema(conn)
    conn.commit()
    results = {}
    for matrix, syllabus, digest in bundles:
        rid = matrix.regulator.id
        if not force and last_loaded_hash(conn, rid) == digest:
            results[rid] = "unchanged"
            continue
        with conn.transaction():
            load(conn, matrix, digest, syllabus)
        results[rid] = "loaded"
    conn.commit()
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="validate the matrices only")
    parser.add_argument("--force", action="store_true", help="reload unchanged matrices too")
    args = parser.parse_args(argv)

    paths = sorted(MATRICES_DIR.glob("*.json"))
    for path in paths:
        m = load_matrix(path)
        print(f"valid  {path.name}: {m.regulator.short_name}, {len(m.requirements)} requirements, "
              f"{len(m.fees)} fees, {len(m.competencies)} competencies, verified {m.verified_on}")
        for q in m.open_questions:
            print(f"       open: {q}")
    for path in sorted(SYLLABI_DIR.glob("*.json")):
        sy = load_syllabus(path)
        print(f"valid  syllabi/{path.name}: {len(sy.disciplines)} disciplines, {len(sy.exams)} exams")
    if args.check:
        return 0

    url = os.environ.get("DATABASE_URL")
    if not url:
        print("DATABASE_URL is not set (see docker-compose.yml).", file=sys.stderr)
        return 2
    import psycopg
    with psycopg.connect(url) as conn:
        for rid, outcome in sync(conn, force=args.force).items():
            print(f"{outcome:9} {rid}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
