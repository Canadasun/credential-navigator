# Roadmap

| Phase | Weeks | Goal |
|---|---|---|
| 1. Regulatory data ingestion | 1–3 | Compile APEGA and CRNA (later ACP and CIPS) registration requirements, fees, application routes and required documents into a relational database. Build crawlers that flag changes on the regulators' sites. |
| 2. Document processing engine | 4–6 | Accept PDF transcripts and syllabi. OCR plus an LLM pipeline extracts course names, credit hours and descriptions, then maps them against the competency data to find gaps. |
| 3. User portal and progress tracking | 7–9 | Next.js dashboard: personal licensing roadmap, missing documents, estimated costs and timelines, step tracking. |
| 4. Safeguards and disclaimers | 10 | Make it clear throughout the UI that this is an advisory tool, that the gap analysis is for preparation only, and that the regulators alone make licensing decisions. |
| 5. Pilot testing and B2G outreach | 11–14 | Beta test with Calgary newcomer-serving agencies (e.g. Calgary Catholic Immigration Society, Centre for Newcomers) before approaching provincial ministries. |

## Status

**Phase 1 done 2026-10-25** (43 tests, 51 pages monitored). Captured from official pages:

- **APEGA:** 3 routes; requirements; 22 competencies with the 8 mandatory minimums and the six category minimum averages; application fees; NPPE ($250, 4 attempts), FE ($75 + US$225 to NCEES) and technical exam ($500) fees; deadlines and review times.
- **CRNA:** 2 routes; requirements including the 5 accepted credential assessment providers; 2026–2027 fees ($183.75 account, $483 permit); NNAS ($750) and NCLEX-RN fees ($360, rising to $570 on Feb. 1, 2027); 101 entry-level competencies in 9 roles.
- **APEGA exam syllabi** (added 2026-10-25): 14 engineering disciplines, 266 exam descriptions, group and Basic Studies rules, in `data-pipeline/syllabi/`.

Not on public pages, or not captured yet:

- APEGA per-competency minimums for the 14 non-mandatory competencies (inside APEGA's assessment tool), the university course-equivalents lists, and the WES fee. The Basic Studies rules come from checklists dated 2020–2021.
- CRNA: the fees of the credential assessment providers and of CNPS liability protection. The entry-level competencies are the March 2019 edition, and their licence covers education, research, private study and reference: ask the CRNA before showing the full text in a commercial product.
- Run `watch_sources.py` weekly once the project has a server or CI.

**Phase 2, first slice done 2026-10-25:** PDF text, course extraction, APEGA syllabus matching and gap report through `POST /apega/analysis` (20 backend tests), with local OCR for scanned documents (Tesseract in the API container). Next: an optional LLM extractor for messy layouts, nursing (CRNA competencies), and calibrating the match thresholds on real, consented documents.

**Phase 3, roadmap API done 2026-10-25:** `POST /roadmap/apega` and `/roadmap/crna` (36 backend tests). **Portal done 2026-10-25:** Next.js questionnaire, roadmap and upload pages, 7 browser checks including accessibility. Next: accounts and saved progress (needs the privacy decisions below).

**Phase 3 extended 2026-10-25:**
- **Pharmacists (ACP):** provisional and clinical registers, PEBC (including the January 2027 pathway change), IELTS Academic/OET at the NAPRA minimums, DCPP, SPT, jurisprudence and 9 fees from ACP, PEBC and Pharmacists' Gateway Canada.
- **Computer science and IT (CIPS I.S.P.):** voluntary designation; years of experience by education, recent hours, SFIA level, review and member fees. The page states that computing work isn't regulated and that only APEGA licenses software engineers.
- **French interface** (UI text; regulator content stays in English with a French notice) and a **privacy page**.
- 64 pages monitored; the monitor now reports bot-check pages as blocked instead of changed. Tests: 49 pipeline, 69+ backend, 11 browser checks and 15 regression scenarios.

Not captured yet: DCPP tuition, the first-attempt Ethics and Jurisprudence Exam fee, whether PEBC fees include tax, the regular CIPS membership fee and the Alberta legislation behind the I.S.P.

**Phase 4 (safeguards):** the advisory banner, per-result disclaimers, the privacy page and the "voluntary designation" wording for CIPS are in place.

**Phase 5 (pilot):** agency demo script and one-page summary in `docs/outreach/`.

## Open decisions

- **LLM:** the original plan named GPT-4o or Claude 3.5 Sonnet, which are now older models. Pick a current model when Phase 2 starts.
- **Next.js routing:** decided: App Router (`frontend/app/`).
- **LlamaIndex vs LangChain:** pick one.
- **Supabase vs AWS RDS:** Supabase also offers auth and storage, which could replace S3.
- **Crawling:** check each regulator's terms of use and robots.txt. Store the source URL and retrieval date with every requirement.
- **Privacy:** transcripts and ID are personal information. Plan consent, retention and deletion, and keep data in Canada (Alberta PIPA, and PIPEDA where it applies).
- **Legal reference:** confirm the exact name and current text of Alberta's fair registration legislation before citing it.
