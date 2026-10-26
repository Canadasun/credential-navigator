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


def regulator(conn, regulator_id: str) -> dict | None:
    row = conn.execute("SELECT id, name, short_name, designation, verified_on FROM regulators WHERE id = %s",
                       (regulator_id,)).fetchone()
    return dict(zip(("id", "name", "short_name", "designation", "verified_on"), row)) if row else None


def pathways(conn, regulator_id: str) -> dict[str, dict]:
    rows = conn.execute("SELECT id, name, summary FROM pathways WHERE regulator_id = %s", (regulator_id,)).fetchall()
    return {r[0]: {"id": r[0], "name": r[1], "summary": r[2]} for r in rows}


def requirements(conn, regulator_id: str, pathway_id: str) -> list[dict]:
    rows = conn.execute(
        "SELECT r.id, r.category, r.title, r.description, r.conditional, r.details, s.url"
        " FROM requirements r JOIN requirement_pathways rp ON rp.regulator_id = r.regulator_id"
        " AND rp.requirement_id = r.id JOIN sources s ON s.regulator_id = r.regulator_id AND s.id = r.source_id"
        " WHERE r.regulator_id = %s AND rp.pathway_id = %s ORDER BY r.position",
        (regulator_id, pathway_id)).fetchall()
    keys = ("id", "category", "title", "description", "conditional", "details", "source_url")
    return [dict(zip(keys, r)) for r in rows]


def fees(conn, regulator_id: str) -> dict[str, dict]:
    rows = conn.execute(
        "SELECT f.id, f.name, f.amount, f.currency, f.gst, f.payee, f.conditional, f.period,"
        " f.effective_from, f.effective_until, s.url FROM fees f JOIN sources s"
        " ON s.regulator_id = f.regulator_id AND s.id = f.source_id WHERE f.regulator_id = %s",
        (regulator_id,)).fetchall()
    keys = ("id", "name", "amount", "currency", "gst", "payee", "conditional", "period",
            "effective_from", "effective_until", "source_url")
    return {r[0]: dict(zip(keys, r), amount=float(r[2])) for r in rows}


def timelines(conn, regulator_id: str) -> list[dict]:
    rows = conn.execute(
        "SELECT t.name, t.max_days, t.business_days, t.description, s.url FROM timelines t JOIN sources s"
        " ON s.regulator_id = t.regulator_id AND s.id = t.source_id WHERE t.regulator_id = %s ORDER BY t.position",
        (regulator_id,)).fetchall()
    return [dict(zip(("name", "max_days", "business_days", "description", "source_url"), r)) for r in rows]
