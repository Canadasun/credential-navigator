"""Read regulatory data (loaded by data-pipeline/update_matrices.py) from PostgreSQL."""
from __future__ import annotations

from services.matching import Exam


def disciplines(conn, regulator_id: str) -> list[dict]:
    rows = conn.execute(
        "SELECT id, name, edition FROM syllabus_disciplines WHERE regulator_id = %s ORDER BY name",
        (regulator_id,)).fetchall()
    return [{"id": r[0], "name": r[1], "edition": r[2]} for r in rows]


def all_exams(conn, regulator_id: str) -> list[Exam]:
    rows = conn.execute(
        "SELECT code, title, description FROM syllabus_exams WHERE regulator_id = %s ORDER BY code",
        (regulator_id,)).fetchall()
    return [Exam(*r) for r in rows]


def discipline_groups(conn, regulator_id: str, discipline_id: str) -> list[dict] | None:
    """Every exam group an applicant in this discipline is assessed against, in syllabus order:
    preliminary, basic studies (compulsory, then optional), discipline groups, complementary."""
    row = conn.execute(
        "SELECT basic_compulsory, basic_optional, basic_optional_required FROM syllabus_disciplines"
        " WHERE regulator_id = %s AND id = %s", (regulator_id, discipline_id)).fetchone()
    if row is None:
        return None
    basic_compulsory, basic_optional, optional_required = row
    rows = conn.execute(
        "SELECT discipline_id, name, kind, required, exams FROM syllabus_groups"
        " WHERE regulator_id = %s AND (discipline_id = %s OR discipline_id IS NULL) ORDER BY id",
        (regulator_id, discipline_id)).fetchall()
    common = [r for r in rows if r[0] is None]
    own = [r for r in rows if r[0] is not None]
    as_group = lambda r: {"name": r[1], "kind": r[2], "required": r[3], "exams": list(r[4])}  # noqa: E731
    groups = [as_group(r) for r in common[:1]]  # preliminary
    groups.append({"name": "Basic Studies (compulsory)", "kind": "compulsory",
                   "required": len(basic_compulsory), "exams": list(basic_compulsory)})
    if optional_required:
        groups.append({"name": "Basic Studies (optional)", "kind": "elective",
                       "required": optional_required, "exams": list(basic_optional)})
    groups += [as_group(r) for r in own]
    groups += [dict(as_group(r), name="Complementary Studies") for r in common[1:]]  # page heading is "All Exams"
    return groups


def source_url(conn, regulator_id: str, discipline_id: str) -> str | None:
    row = conn.execute(
        "SELECT s.url FROM syllabus_disciplines d JOIN sources s ON s.regulator_id = d.regulator_id"
        " AND s.id = d.source_id WHERE d.regulator_id = %s AND d.id = %s", (regulator_id, discipline_id)).fetchone()
    return row[0] if row else None
