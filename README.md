# Credential Navigator

An advisory tool that helps internationally trained engineers, nurses, pharmacists and computing professionals prepare for licensing or certification in Alberta. Applicants upload their transcripts and course syllabi. The platform pulls out their courses, compares them with the regulators' competency requirements, and shows a personal roadmap: which documents are missing, the likely gaps, the fees and the expected timelines.

It covers APEGA (engineering), the CRNA (nursing), the Alberta College of Pharmacy (ACP, pharmacists) and CIPS (the voluntary I.S.P. designation for computer science and IT). Each profession is a regulator matrix plus a small set of status rules, without changing the core application. The portal is in English and French.

> **Advisory only.** The roadmaps and gap analysis are for preparation. APEGA, the CRNA, the ACP and CIPS alone decide on registration or certification.

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
  crawlers/       Monitor the regulators' pages for fee and timeline changes
  matrices/       Competency requirements as JSON
docs/             Roadmap and decisions
```

**Run it:** with Docker Desktop running, `./scripts/start.sh` builds and starts the database, data loader, API and portal, then opens http://localhost:3010 (`--stop`, `--reset`, `--no-open`). The scenarios to try and the results to expect are in [docs/test-guide.html](docs/test-guide.html).

The roadmap is in [docs/ROADMAP.md](docs/ROADMAP.md).

GitHub Actions (`.github/workflows/ci.yml`) runs the data-pipeline, API (including OCR) and portal browser tests on every push, and every Monday checks the regulators' pages against the committed baseline; a changed page fails the run so a person re-reads it.

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
- **Scanned PDFs are read with local OCR** (Tesseract, English and French) when the API runs in its Docker image: `docker compose up -d --build api`, then http://127.0.0.1:8010/docs. Nothing leaves the machine. The response reports the OCR confidence and asks the applicant to check the course list. Without Tesseract (plain `uvicorn`), scanned PDFs are refused with a clear message. Uploads are not stored: a file, and the page images made for OCR, may pass through temporary files that are deleted when the request ends.
- Every response carries the advisory disclaimer. Titles alone give a rough comparison, and the response says so.
- The test documents in `backend/tests/fixtures/` are synthetic (a fictional university).

## Personal roadmap (Phase 3, API)

`POST /roadmap/apega`, `/roadmap/crna`, `/roadmap/acp` and `/roadmap/cips` take an applicant's answers (every field optional; see `/docs`) and return the recommended route, each requirement marked done, to do, to confirm or may apply, the next steps, expected and possible costs with totals per currency, and the regulator's timelines. Every item links to the regulator page it came from. Thresholds such as 48 months of experience, 450 practice hours or IELTS minimums come from the regulator data, not the code, and the NCLEX-RN fee switches automatically on its effective date. Unknown answers become questions, never guesses. Answers are not stored on the server.

- **Pharmacists (ACP):** two stages, the provisional (intern) register and then the clinical register; each requirement is labelled with its stage. PEBC Document Evaluation and Qualifying Exam (with the January 2027 change: Part I before Part II), IELTS Academic or OET at the NAPRA minimums (OET letter grades are ranked E to A), the University of Alberta DCPP unless both PEBC parts were passed on the first attempt, Structured Practical Training (two experiences of 320+ hours), jurisprudence and liability insurance. A US ACPE-accredited PharmD is a separate route without the DCPP.
- **Computer science and IT (CIPS):** computing work isn't regulated in Alberta, so this roadmap is for the voluntary I.S.P. The years of experience needed depend on the education (a foreign computer science degree counts as a non-accredited four-year degree: 4 years; any other background: 8), plus 1,000 hours in the last 12 months and SFIA level 3. The roadmap says that only APEGA licenses software engineers.

## Applicant portal (Phase 3)

`frontend/` is a Next.js 15 app (App Router, Tailwind CSS 4, TypeScript). The home page leads to **Engineering (APEGA)**, **Nursing (CRNA)**, **Pharmacy (ACP)** and **Computing (CIPS)**: a short questionnaire where every answer can be "Not sure", the roadmap (route, progress, next steps, requirements with sources, costs, timelines), and for engineers the course-description or transcript upload with the gap report. The browser calls `/api/*`, which Next.js forwards to the API (`API_URL`, default http://127.0.0.1:8010), so no cross-origin setup is needed. An advisory note is on every page.

```bash
docker compose up -d --build api          # API with OCR on 127.0.0.1:8010
cd frontend && npm install && npm run build && npm run start   # http://127.0.0.1:3010
node tests/e2e.cjs                        # browser test (visible Chromium; HEADLESS=1 to hide)
HEADLESS=1 node tests/regressions.cjs      # state, validation, drafts, export, mobile and accessibility regressions
```

The browser test needs `playwright` and `@axe-core/playwright` (`npm install --no-save playwright @axe-core/playwright`). It runs the engineering, nursing, pharmacy and computing flows, the text, scanned and blank-scan uploads, the privacy page, the French interface, an axe accessibility audit (no serious or critical issues) and a phone-width check on every page.

## Usability and input validation

The portal groups questions into sections, marks the active profession and provides jump links to results and costs. Submission status is announced and focus moves to a ready result. Changing an answer, file or discipline cancels in-flight work and clears the old report; only the latest request can own the result.

Answers are not saved to the server. Applicants can explicitly opt into a local browser draft, restore it on reload, and delete it from the form. Draft saving is off by default and never includes uploaded files. Shared-browser users can leave it off. Reports support browser print/save-PDF and local JSON download. Course comparisons identify the selected document and discipline and expose the shared terms behind a match; these are text-similarity explanations, not regulator decisions.

The API rejects future English-test dates, invalid score ranges/steps and conflicting test-plus-exemption evidence. IELTS inputs use 0–9 in half bands ([official score scale](https://ielts.org/take-a-test/your-results/ielts-scoring-in-detail)); CELBAN inputs use whole CLB levels within the 0–12 input envelope and no overall field. Unknown bands remain missing instead of being inferred. Existing licensing minimums remain in the regulatory data. Leap-day expiration anniversaries clamp to February's last calendar day rather than throwing an exception; the roadmap remains advisory.

**French.** A button in the menu switches the interface to French (Canada); the choice is remembered in the browser, and a French browser starts in French. The requirements, fees and advice come from the regulators' English pages and stay in English, with a French note saying so and `lang="en"` on that text for screen readers. Every interface string is in `frontend/lib/messages/`; the French file must have every English key, which the type check enforces.

**Privacy.** `/privacy` (linked in every footer, in both languages) explains what is processed and what is never kept: no accounts, no cookies, no analytics, no outside AI service, uploads deleted after reading.

See [docs/UI_REVIEW_FIXES.md](docs/UI_REVIEW_FIXES.md) for the review findings, fixes and validation record. The original browser suite now checks every route at 320, 375 and 768 px; CI also runs the new regression suite.

## Copyright and third-party content

Copyright © 2026 Idowu Peter Ayeni. All rights reserved; no licence is granted to use, copy or distribute this code.

The regulatory information in `data-pipeline/matrices/` and `data-pipeline/syllabi/` (requirements, fees, competencies, exam syllabi) is taken from the public websites of APEGA, the CRNA, NNAS, NCSBN, the ACP, PEBC, NAPRA and CIPS, belongs to those organizations, and is included for reference with a link to each source. This project is not affiliated with or endorsed by any of them.
