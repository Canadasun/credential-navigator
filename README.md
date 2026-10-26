# Credential Navigator

An advisory tool that helps internationally trained engineers and nurses prepare for licensing in Alberta. Applicants upload their transcripts and course syllabi. The platform pulls out their courses, compares them with the regulators' competency requirements, and shows a personal roadmap: which documents are missing, the likely gaps, the fees and the expected timelines.

It covers APEGA (engineering) and CRNA (nursing) to start. Other professions are added as new competency matrices, without changing the core application.

> **Advisory only.** The gap analysis is for preparation. APEGA and CRNA alone decide on licensing.

## Design principle

Regulatory rules live in a verified, structured database: requirements, fees, timelines and forms. The AI never "knows" the rules. It only reads the applicant's own documents (course names, credit hours, descriptions), and matching against requirements is done with database queries. This keeps the requirements free of hallucinations and lets the LLM provider change without touching the rules.

## Stack (proposed)

| Layer | Choice | Purpose |
|---|---|---|
| Frontend | Next.js (React) + Tailwind CSS | Applicant portal, dashboard, progress tracking |
| Backend | Python, FastAPI | Auth, uploads, analysis API, async jobs |
| Document AI | LlamaIndex or LangChain + an LLM (Claude or GPT) | Extract courses from transcripts and syllabi |
| OCR | AWS Textract (or a PDF text parser for digital PDFs) | Read scanned documents |
| Database | PostgreSQL (Supabase or AWS RDS) | Profiles, application status, regulatory requirements |
| File storage | AWS S3 with signed URLs | Degrees, ID and transcripts |
| Local dev | Docker Compose | Run everything on one machine |

## Layout

```
frontend/         Next.js web app
  components/     Reusable UI (DocumentUploader, ProgressTracker)
  pages/          Routes (/dashboard, /engineering, /nursing)
  lib/            API client and utilities
backend/          FastAPI server
  api/            Route handlers (auth, documents, analysis)
  core/           Security, configuration, database connections
  services/       LLM orchestration, PDF parsing and OCR
  models/         Pydantic models and SQLAlchemy schemas
data-pipeline/    Regulatory data
  crawlers/       Monitor APEGA/CRNA pages for fee and timeline changes
  matrices/       Competency requirements as JSON
docs/             Roadmap and decisions
```

The roadmap is in [docs/ROADMAP.md](docs/ROADMAP.md).

## Regulatory data (Phase 1)

`data-pipeline/matrices/` holds one JSON file per regulator: pathways, requirements, documents, fees, timelines and competencies. Every item cites the official page it came from and the date it was read. `matrix_models.py` validates them: every source and pathway reference must resolve, fees must be positive and say whether GST is included, and mandatory competencies need a minimum level. Facts that haven't been captured yet are listed under `open_questions` instead of being guessed.

```bash
python3 -m venv .venv && .venv/bin/pip install -r data-pipeline/requirements.txt
docker compose up -d db
cd data-pipeline
../.venv/bin/python update_matrices.py --check        # validate only
export DATABASE_URL=postgresql://navigator:navigator-local-only@127.0.0.1:5433/navigator
../.venv/bin/python update_matrices.py                # load changed matrices into PostgreSQL
../.venv/bin/python crawlers/watch_sources.py         # which regulator pages changed?
TEST_DATABASE_URL=$DATABASE_URL ../.venv/bin/python -m unittest discover -s tests -v
```

`syllabi/apega_engineering.json` holds APEGA's exam syllabi: for each of 14 engineering disciplines, the compulsory and elective exam groups and how many are required, the Basic Studies rules, and the description of all 266 exams. These are what the Board of Examiners assigns when a degree isn't accredited, so Phase 2 matches applicants' courses against them. `crawlers/apega_syllabi.py` rebuilds the file from APEGA's pages and assessment checklists (`--check` reports differences); a person reviews the diff before committing.

`update_matrices.py` loads each changed regulator, with its syllabus, in one transaction, and a single invalid file loads nothing. `watch_sources.py` compares each cited page's main content with `crawlers/snapshots.json`, respects robots.txt, and exits 1 when a page changed or disappeared. It never edits the matrices: a person re-reads the page, updates the JSON, and runs `--update` to accept the new baseline.

## Academic gap analysis (Phase 2, first slice)

`backend/` is a FastAPI service. Upload a text-based PDF of course descriptions (or a transcript) and pick an APEGA discipline; it returns, for each exam group in that discipline's syllabus, which exams look covered by which course, which look like gaps, and the shared terms behind each match.

```bash
.venv/bin/pip install -r backend/requirements.txt
cd backend
../.venv/bin/uvicorn main:app --reload          # http://127.0.0.1:8000/docs
curl -F discipline=mechanical-engineering -F file=@tests/fixtures/mechanical_course_descriptions.pdf \
     http://127.0.0.1:8000/apega/analysis
DATABASE_URL=postgresql://navigator:navigator-local-only@127.0.0.1:5433/navigator \
     ../.venv/bin/python -m unittest discover -s tests -v
docker compose exec -T api python -m unittest discover -s tests   # includes the OCR tests
```

- **No AI model yet.** Courses are found by their codes (one course per line, as in most transcripts and course calendars), and matched by TF-IDF similarity against APEGA's exam descriptions. It runs offline and every result is explainable.
- **Each course counts toward one exam**, and compulsory exams get first claim on courses, as in an academic assessment.
- **Scanned PDFs are read with local OCR** (Tesseract, English and French) when the API runs in its Docker image: `docker compose up -d --build api`, then http://127.0.0.1:8010/docs. Nothing leaves the machine. The response reports the OCR confidence and asks the applicant to check the course list. Without Tesseract (plain `uvicorn`), scanned PDFs are refused with a clear message. Uploads are processed in memory and not stored.
- Every response carries the advisory disclaimer. Titles alone give a rough comparison, and the response says so.
- The test documents in `backend/tests/fixtures/` are synthetic (a fictional university).
