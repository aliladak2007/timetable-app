# Timetabling Assistant Repo-Ready Prompt Pack

This pack is designed for use with Codex or similar coding agents to build a tutoring-centre timetabling assistant.

## Included files
- `01_master_prompt.txt` — full product + implementation prompt
- `02_phase1_prompt.txt` — backend-first scoped prompt
- `03_phase2_prompt.txt` — frontend/admin UI prompt
- `04_phase3_prompt.txt` — polish, deployment, and quality prompt
- `AGENTS.md` — persistent repo instructions for the coding agent
- `PRODUCT_SPEC.md` — concise product spec for the repository
- `SCHEMA_BRIEF.md` — recommended data model and scheduling rules
- `TEST_PLAN.md` — test cases and quality expectations

## Suggested use
1. Create a new repository.
2. Add `AGENTS.md`, `PRODUCT_SPEC.md`, `SCHEMA_BRIEF.md`, and `TEST_PLAN.md` to the repo root.
3. Paste `01_master_prompt.txt` into Codex for the first run.
4. Use `02_phase1_prompt.txt`, `03_phase2_prompt.txt`, and `04_phase3_prompt.txt` in order for follow-up runs.
5. Ask the agent to commit after each completed phase.

## Recommended stack
- Backend: Python + FastAPI
- Frontend: React or Next.js
- Database: SQLite for MVP
- ORM: SQLAlchemy
- Tests: pytest

## Product framing
This is not a university timetable generator and not a school ERP.
It is a tutoring-centre scheduling assistant with a matching engine.
