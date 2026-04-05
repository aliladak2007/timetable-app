# Timetabling Assistant

Timetabling Assistant is now structured as a secured FastAPI backend, a static-exportable Next.js admin frontend, and a Tauri desktop shell for Windows packaging. The app keeps the original recurring weekly matching workflow, but adds authentication, RBAC, PostgreSQL, audit logging, schedule exceptions, closures, leave handling, and standards-based calendar export.

## Current Architecture

- `backend/`
  FastAPI API, SQLAlchemy models, Alembic migrations, auth, audit logging, matching engine, scheduling exceptions, CSV/ICS export, and legacy SQLite import tooling.
- `frontend/`
  Next.js 15 admin UI using static export so it can be bundled by Tauri while keeping the existing web dev workflow.
- `src-tauri/`
  Windows desktop shell that starts the Python backend sidecar, waits for readiness, and shuts it down with the app.
- `scripts/`
  Packaging scripts for the Python sidecar and the Tauri desktop build.

## Security Posture

- No default admin credentials are shipped.
- First-run bootstrap creates the initial admin account.
- Passwords are hashed with Argon2.
- Role-based access control supports `admin`, `staff_scheduler`, and `viewer`.
- Sensitive API routes require auth and role checks.
- Login attempts are rate limited in-process.
- Structured audit logs record auth, user administration, recurring schedule changes, exception changes, and calendar feed creation.
- FastAPI docs are disabled outside development by default.
- Request size limits and defensive response headers are enabled.

Residual risks and hardening notes are documented in [SECURITY.md](/C:/Users/mahmo/Downloads/timetable-app/SECURITY.md).

## Scheduling Model

The base recurring timetable still lives in `sessions`, but the app now separates date-specific changes from the base weekly pattern:

- `sessions`
  Recurring weekly templates.
- `session_occurrence_exceptions`
  One-off occurrence overrides such as cancellation, completion, missed lessons, holiday flags, or reschedules.
- `centre_closures`
  Centre-wide holidays and closure windows.
- `teacher_leave_blocks`
  Teacher leave or date-bound unavailability.
- `student_absence_blocks`
  Student absence or date-bound unavailability.

Occurrences are generated for a requested date range by combining the recurring template with exception records and operational blocks.

## Local Development

### 1. Start PostgreSQL

```powershell
docker compose up -d postgres
```

### 2. Configure the environment

```powershell
Copy-Item .env.example .env
```

### 3. Install backend dependencies

```powershell
cd backend
py -m pip install -r requirements.txt
```

### 4. Run migrations

```powershell
cd backend
py -m alembic upgrade head
```

### 5. Start the backend

```powershell
cd backend
uvicorn app.main:app --reload
```

### 6. Start the frontend

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

### 7. First admin bootstrap

Open `http://localhost:3000`, create the first admin account, then sign in.

## Desktop Packaging

The preferred packaged architecture is:

- Tauri shell
- static frontend bundle from `frontend/out`
- Python backend packaged as a Windows sidecar executable
- local backend started automatically in the background

### Build the packaged backend sidecar

```powershell
.\scripts\build-backend-sidecar.ps1
```

### Build the Windows desktop installer

```powershell
.\scripts\build-desktop.ps1
```

Expected Tauri outputs:

- installer and bundle artifacts under [src-tauri/target/release/bundle](/C:/Users/mahmo/Downloads/timetable-app/src-tauri/target/release/bundle)

## Database Migration From Legacy SQLite

The old SQLite schema is no longer the production target. To import legacy data:

```powershell
cd backend
py -m alembic upgrade head
py -m app.import_legacy_sqlite .\timetabling.db
```

This migrates teachers, students, availability, preferences, blocked times, and recurring sessions into PostgreSQL without silently dropping data.

## Calendar Support

Implemented support:

- authenticated ICS export for teacher calendars
- authenticated ICS export for student calendars
- authenticated CSV export for recurring sessions
- private feed token creation for subscription-style calendar feeds

Notes and limitations are documented in [CALENDAR_INTEGRATION.md](/C:/Users/mahmo/Downloads/timetable-app/CALENDAR_INTEGRATION.md).

## Operational Docs

- [ADMIN_SETUP.md](/C:/Users/mahmo/Downloads/timetable-app/ADMIN_SETUP.md)
- [SECURITY.md](/C:/Users/mahmo/Downloads/timetable-app/SECURITY.md)
- [CALENDAR_INTEGRATION.md](/C:/Users/mahmo/Downloads/timetable-app/CALENDAR_INTEGRATION.md)
