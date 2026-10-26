# Roadmap

| Phase | Weeks | Goal |
|---|---|---|
| 1. Regulatory data ingestion | 1–3 | Compile APEGA and CRNA registration requirements, fees, application routes and required documents into a relational database. Build crawlers that flag changes on the regulators' sites. |
| 2. Document processing engine | 4–6 | Accept PDF transcripts and syllabi. OCR plus an LLM pipeline extracts course names, credit hours and descriptions, then maps them against the competency data to find gaps. |
| 3. User portal and progress tracking | 7–9 | Next.js dashboard: personal licensing roadmap, missing documents, estimated costs and timelines, step tracking. |
| 4. Safeguards and disclaimers | 10 | Make it clear throughout the UI that this is an advisory tool, that the gap analysis is for preparation only, and that APEGA/CRNA alone make licensing decisions. |
| 5. Pilot testing and B2G outreach | 11–14 | Beta test with Calgary newcomer-serving agencies (e.g. Calgary Catholic Immigration Society, Centre for Newcomers) before approaching provincial ministries. |

## Status

**Phase 1 done 2026-10-25** (31 tests). Captured from official pages:

- **APEGA:** 3 routes; requirements; 22 competencies with the 8 mandatory minimums and the six category minimum averages; application fees; NPPE ($250, 4 attempts), FE ($75 + US$225 to NCEES) and technical exam ($500) fees; deadlines and review times.
- **CRNA:** 2 routes; requirements including the 5 accepted credential assessment providers; 2026–2027 fees ($183.75 account, $483 permit); NNAS ($750) and NCLEX-RN fees ($360, rising to $570 on Feb. 1, 2027); 101 entry-level competencies in 9 roles.

Not on public pages, or not captured yet:

- APEGA per-competency minimums for the 14 non-mandatory competencies (inside APEGA's assessment tool), discipline syllabi and the technical-exam course equivalents (needed for Phase 2 course matching), and the WES fee.
- CRNA: the fees of the credential assessment providers and of CNPS liability protection. The entry-level competencies are the March 2019 edition, and their licence covers education, research, private study and reference: ask the CRNA before showing the full text in a commercial product.
- Run `watch_sources.py` weekly once the project has a server or CI.

## Open decisions

- **LLM:** the original plan named GPT-4o or Claude 3.5 Sonnet, which are now older models. Pick a current model when Phase 2 starts.
- **Next.js routing:** the layout uses `pages/`. New Next.js projects default to the App Router (`app/`). Decide before Phase 3.
- **LlamaIndex vs LangChain:** pick one.
- **Supabase vs AWS RDS:** Supabase also offers auth and storage, which could replace S3.
- **Crawling:** check each regulator's terms of use and robots.txt. Store the source URL and retrieval date with every requirement.
- **Privacy:** transcripts and ID are personal information. Plan consent, retention and deletion, and keep data in Canada (Alberta PIPA, and PIPEDA where it applies).
- **Legal reference:** confirm the exact name and current text of Alberta's fair registration legislation before citing it.
