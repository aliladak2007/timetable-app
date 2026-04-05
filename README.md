# Timetabling Assistant

## Overview
Timetabling Assistant is a scheduling and operations workspace for tutoring or lesson-based timetables. It combines a secured FastAPI backend, a static-exportable Next.js admin frontend, and a Windows Tauri desktop shell that can run the backend locally as a packaged sidecar.

The app is built for small teams or operators who need to manage:
- teacher availability
- student preferences and blocked times
- recurring weekly lesson templates
- date-specific cancellations, completions, misses, and reschedules
- closures, holidays, leave, and absences
- calendar exports for operational visibility

It is designed to support both:
- local development with PostgreSQL
- packaged desktop use where the backend runs locally and defaults to a local SQLite database

## Key Features
- Windows desktop packaging with Tauri and a bundled Python backend sidecar
- First-run bootstrap flow for creating the initial administrator account
- JWT-based login with role-based access control
- Teacher-linked scoped access for non-admin users
- Teacher directory with editable weekly availability windows
- Student directory with editable preferred windows and blocked times
- Recurring weekly session templates with validation against teacher availability and student conflicts
- Matching workflow that ranks candidate weekly lesson slots
- Occurrence-level exception handling for `cancelled`, `completed`, `missed`, `rescheduled`, and `holiday_affected`
- Operational blocks for centre closures, holidays, teacher leave, and student absences
- Dashboard summaries with upcoming occurrences and conflict watchlists
- CSV export of recurring session templates
- ICS calendar export for teachers and students
- Private calendar feed token generation for subscription-style ICS feeds
- Audit logging for auth, user administration, scheduling changes, and calendar feed operations
- Legacy SQLite import utility for migrating older local data into the current schema

## Architecture
The repository is split into three main runtime layers:

- `backend/`: FastAPI application, SQLAlchemy models, Alembic migrations, auth, access control, matching logic, scheduling logic, exports, and tests
- `frontend/`: Next.js 15 frontend with static export enabled via `output: "export"`
- `src-tauri/`: Windows desktop shell that starts the packaged backend sidecar, waits for readiness, and exposes the runtime API base URL to the frontend

### Development Mode
In development, the expected setup is:
- PostgreSQL running locally, typically via Docker Compose
- FastAPI served with Uvicorn
- Next.js running in dev mode on `http://localhost:3000`

### Packaged Desktop Mode
In packaged desktop mode:
- the Tauri shell launches a bundled Python backend executable
- the backend binds to a random localhost port
- the frontend reads that runtime API base URL through a Tauri command
- if no explicit database URL is configured, the backend defaults to a local SQLite database in the app config directory
- the backend auto-creates schema in desktop mode

This means the packaged app is currently a local desktop deployment model, not a shared hosted deployment.

## Access Model
The app has three user roles:

- `admin`
- `staff_scheduler`
- `viewer`

### Admin
Admins have global access across the dataset and can:
- manage users and role assignments
- create and revoke private calendar feed tokens
- manage closures and other operations data
- access audit logs
- create, edit, and delete teachers, students, and sessions

### Scoped Non-Admin Users
Non-admin users must be linked to a teacher through `linked_teacher_id`.

That teacher link is not just a UI filter. It is enforced in backend access helpers and query scoping:
- teachers are limited to the linked teacher
- sessions are limited to sessions owned by the linked teacher
- students are limited to students who are attached to that teacher's sessions
- teacher leave, student absences, occurrence queries, and calendar exports are scoped the same way

If a non-admin user is not linked to a teacher, login is denied.

### Backend Authorization vs UI Capabilities
The frontend changes navigation and controls based on role, but backend authorization is enforced independently through FastAPI dependencies and scoped query helpers.

That distinction matters because:
- hiding an action in the UI is not the security boundary
- the security boundary is the backend token validation, role checks, and teacher-linked scoping

## Scheduling Model
The app separates recurring weekly planning from date-specific operational changes.

### Recurring Session Templates
Recurring lessons live in `sessions` and include:
- teacher
- student
- weekday
- start and end minute
- duration
- subject
- start date
- optional end date
- active or inactive status

Session creation validates:
- the session fits inside teacher availability
- the teacher is not already booked for an overlapping recurring slot
- the student is not already booked for an overlapping recurring slot
- the slot does not intersect the student's blocked times

### Occurrence-Level Exceptions
Date-specific changes live in `session_occurrence_exceptions`. Supported statuses are:
- `cancelled`
- `completed`
- `rescheduled`
- `missed`
- `holiday_affected`

Reschedules can carry:
- a new date
- a new start minute
- a new end minute

Reschedule validation checks for:
- centre closures and holidays
- teacher leave
- student absences
- conflicts with other scheduled lessons on the target date

### Closures, Leave, and Absences
Operational blocks are stored separately:
- `centre_closures`
- `teacher_leave_blocks`
- `student_absence_blocks`

Occurrence generation combines recurring sessions with:
- closure windows
- leave blocks
- student absence blocks
- saved occurrence exceptions

This lets the app produce an occurrence view without rewriting the underlying recurring template.

### Matching Workflow
The matching engine ranks weekly slot suggestions by intersecting:
- teacher availability
- student preferred windows
- student blocked times
- existing active sessions

It scores candidates using:
- preference priority
- adjacency to existing teacher sessions
- adjacency to existing student sessions
- an earlier-slot bonus

The current frontend workflow uses that engine during the "add new student" flow:
1. capture student profile, preferred windows, and blocked times
2. request ranked suggestions from the backend
3. choose a slot
4. create the student, recurring session, and student constraints

## Calendar / Export Support
Implemented export support includes:

- CSV export of recurring session templates
- ICS export for a teacher calendar
- ICS export for a student calendar
- private token-based ICS calendar feeds

### ICS Exports
ICS files are generated from occurrence data, not just base recurring templates. That means exported calendars reflect:
- reschedules
- cancellations
- closure impact
- leave and absence impact

ICS generation uses the configured application timezone, which defaults to `Europe/London`.

### Private Feed Tokens
Admins can create private feed tokens stored as hashed secrets in the database. The feed URL is bearer-style:
- possession of the URL grants access to that feed
- revocation is handled by marking the token inactive

### Current Export Limitations
- the UI currently creates private feed URLs only for centre-wide feeds
- teacher and student ICS exports are file downloads rather than long-lived feed management in the UI
- there is no direct Google Calendar or Outlook API sync yet

## Tech Stack
- Backend: FastAPI
- ORM: SQLAlchemy 2.x
- Migrations: Alembic
- Database: PostgreSQL in development, SQLite fallback in packaged desktop mode
- Auth: JWT with `PyJWT`
- Password hashing: `argon2-cffi`
- Calendar generation: `icalendar`
- Frontend: Next.js 15, React 19
- Frontend packaging model: static export
- Desktop shell: Tauri 2
- Desktop runtime language for shell: Rust
- Backend packaging: PyInstaller
- Tests: `pytest` for backend, Node-based script tests for frontend auth transport
- Local dev services: Docker Compose for PostgreSQL

## Project Structure
```text
backend/
  app/
    api/routes/         FastAPI route handlers
    core/               settings, DB wiring, security
    models/             SQLAlchemy models
    schemas/            Pydantic request/response models
    services/           matching, scheduling, audit, calendar, access logic
  alembic/              database migrations
  tests/                backend test suite
  run_desktop.py        packaged desktop backend entrypoint

frontend/
  app/                  Next.js app router pages
  components/           auth shell, boards, editors, shared UI
  lib/                  API client, auth transport, role helpers
  tests/                frontend logic tests

src-tauri/
  src/main.rs           desktop shell, sidecar launch, runtime config
  tauri.conf.json       Tauri packaging config
  capabilities/         desktop permission set

scripts/
  build-backend-sidecar.ps1
  build-desktop.ps1
```

## Development Setup
### Prerequisites
- Python with `py` launcher available
- Node.js and npm
- Docker Desktop or another Docker runtime
- Rust toolchain for desktop builds

### 1. Start PostgreSQL
From the repository root:

```powershell
docker compose up -d postgres
```

### 2. Create the environment file
```powershell
Copy-Item .env.example .env
```

The default `.env.example` points the backend at a local PostgreSQL instance and the frontend at `http://127.0.0.1:8000/api`.

### 3. Install backend dependencies
```powershell
cd backend
py -m pip install -r requirements.txt
```

### 4. Run database migrations
```powershell
cd backend
py -m alembic upgrade head
```

### 5. Start the backend
```powershell
cd backend
uvicorn app.main:app --reload
```

### 6. Install frontend dependencies
```powershell
cd frontend
npm.cmd install
```

### 7. Start the frontend
```powershell
cd frontend
npm.cmd run dev
```

### 8. Complete first-run bootstrap
Open:

```text
http://localhost:3000
```

If no users exist yet, the app will prompt you to create the initial admin account.

### Docker Compose Alternative
The repository also includes a Compose setup for backend, frontend, and PostgreSQL together:

```powershell
docker compose up --build
```

## Desktop Build
The Windows desktop build sequence is:

1. package the Python backend sidecar with PyInstaller
2. build the static frontend bundle
3. build the Tauri Windows application and installer

### Build the backend sidecar only
```powershell
.\scripts\build-backend-sidecar.ps1
```

### Build the complete desktop app
```powershell
.\scripts\build-desktop.ps1
```

That script performs:
- backend sidecar build
- frontend `npm.cmd run build`
- `cargo tauri build`

### Installer output
The generated Windows installer is written under:

[`src-tauri/target/release/bundle/nsis`](/C:/Users/mahmo/Downloads/timetable-app/src-tauri/target/release/bundle/nsis)

Typical output filename:

```text
Timetabling Assistant_0.1.0_x64-setup.exe
```

## Testing
### Backend tests
```powershell
cd backend
py -m pytest
```

The backend test suite covers:
- auth and bootstrap flows
- role and teacher-scope enforcement
- matching behavior
- occurrence generation and scheduling validation
- calendar generation and desktop runtime defaults
- CORS behavior for desktop packaging

### Frontend tests
```powershell
cd frontend
npm.cmd test
```

The current frontend test coverage is focused on auth transport and token handling logic.

## Security Notes
- No default admin credentials are shipped
- The first user must be created through the bootstrap flow
- Passwords are hashed with Argon2
- Auth uses JWT bearer tokens signed with a generated or configured secret
- Sessions can be invalidated by incrementing `session_version`
- Disabled users and stale sessions are rejected at the API layer
- Non-admin users must be linked to a teacher or login is denied
- Scoped access is enforced in backend query helpers, not just the frontend
- Audit logs record sensitive operational and auth actions
- API docs are disabled outside development by default
- Request-size limits and defensive response headers are enabled

Important caveat:
- the app currently stores calendar feed access as bearer-style URLs; anyone with the active token URL can read that feed until it is revoked

## Known Limitations
- The packaged desktop workflow is currently Windows-focused; the repository is not yet set up as a cross-platform desktop product
- The packaged app is currently a local-instance deployment model, not a shared multi-user hosted system
- Session conflict checks and reschedule conflict checks are application-level validations rather than database-level locking or exclusion constraints
- The matching engine is intentionally heuristic and preference-driven; it does not solve a global optimization problem across the full timetable
- Viewer UX is read-only in the frontend, but the backend still permits the match suggestion endpoint for viewer tokens with valid scope
- Centre-wide private feed creation is exposed in the UI, but feed management for teacher- or student-specific subscription feeds is not yet surfaced as a complete admin workflow
- There is no built-in backup/restore workflow for packaged desktop data yet
- There is no direct external calendar sync with Google Calendar, Outlook, or Exchange
- The ownership model is teacher-linked for scoped users; there is no richer branch, team, or region-based access model yet

## Future Features / Roadmap
The items below are not implemented yet. They are realistic next steps based on the current architecture.

### Multi-Instance / Server-Backed Operation
Today, the packaged app can run as a local desktop app with its own local backend and database.

A future server-backed mode could allow:
- multiple desktop app instances to talk to one central backend
- multiple staff devices to share the same live database
- real-time coordination across users instead of isolated local installs
- centralised management, backups, and operations
- phone or remote-device access to the same underlying schedule data

In practical terms, that would mean replacing the current local-only packaged deployment model with a hosted backend and shared database that multiple clients can reach at the same time.

### Additional Roadmap Items
- hosted deployment mode alongside local desktop mode
- remote access from multiple devices
- stronger concurrency protection for schedule creation and rescheduling conflicts
- richer teacher-student assignment and case ownership models
- Google Calendar and Outlook calendar sync
- notifications and reminders
- reporting and invoicing integrations
- backup and restore workflows for packaged desktop deployments
- broader role expansion such as teacher self-service or parent-facing portals
- more complete calendar feed management UI for teacher and student feeds

## Release Notes / Versioning
Current packaged version: `0.1.0`

Current maturity: early production-oriented alpha.

The repository already includes:
- a real database schema and migrations
- a desktop packaging pipeline
- auth, scoping, and audit controls
- automated backend tests

It is beyond prototype stage, but it is still an early release and should be treated as an actively evolving codebase rather than a finished multi-tenant scheduling platform.
