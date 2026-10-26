# Roadmap

| Phase | Weeks | Goal |
|---|---|---|
| 1. Regulatory data ingestion | 1–3 | Compile APEGA and CRNA registration requirements, fees, application routes and required documents into a relational database. Build crawlers that flag changes on the regulators' sites. |
| 2. Document processing engine | 4–6 | Accept PDF transcripts and syllabi. OCR plus an LLM pipeline extracts course names, credit hours and descriptions, then maps them against the competency data to find gaps. |
| 3. User portal and progress tracking | 7–9 | Next.js dashboard: personal licensing roadmap, missing documents, estimated costs and timelines, step tracking. |
| 4. Safeguards and disclaimers | 10 | Make it clear throughout the UI that this is an advisory tool, that the gap analysis is for preparation only, and that APEGA/CRNA alone make licensing decisions. |
| 5. Pilot testing and B2G outreach | 11–14 | Beta test with Calgary newcomer-serving agencies (e.g. Calgary Catholic Immigration Society, Centre for Newcomers) before approaching provincial ministries. |

## Status

**Phase 1, first pass done 2026-10-25.** APEGA (P.Eng.) and CRNA (RN, internationally educated) matrices, PostgreSQL schema and loader, page-change monitor, 24 tests. Still to capture:

- APEGA: minimum levels for the non-mandatory competencies (Competency Scoring page), the discipline syllabi for course matching, and NPPE/FE exam fees.
- CRNA: the 2026–2027 fee schedule (the matrix holds the 2025–2026 amounts), the list of approved credential assessment services, NNAS and NCLEX-RN fees, and the entry-level RN competencies for course matching.
- Run `watch_sources.py` on a schedule (weekly) once the project has a server or CI.

## Open decisions

- **LLM:** the original plan named GPT-4o or Claude 3.5 Sonnet, which are now older models. Pick a current model when Phase 2 starts.
- **Next.js routing:** the layout uses `pages/`. New Next.js projects default to the App Router (`app/`). Decide before Phase 3.
- **LlamaIndex vs LangChain:** pick one.
- **Supabase vs AWS RDS:** Supabase also offers auth and storage, which could replace S3.
- **Crawling:** check each regulator's terms of use and robots.txt. Store the source URL and retrieval date with every requirement.
- **Privacy:** transcripts and ID are personal information. Plan consent, retention and deletion, and keep data in Canada (Alberta PIPA, and PIPEDA where it applies).
- **Legal reference:** confirm the exact name and current text of Alberta's fair registration legislation before citing it.
