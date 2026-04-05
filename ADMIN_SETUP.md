# Admin Setup

## First Run

1. Start PostgreSQL and apply migrations.
2. Launch the frontend or packaged desktop app.
3. The app will show the bootstrap form if no users exist.
4. Create the first admin account with a strong password.
5. Sign in and create any additional scheduler or viewer accounts from the admin user screen when added to your workflow.

## Recommended Roles

- `admin`
  Full access, user management, security-sensitive configuration, audit review.
- `staff_scheduler`
  Day-to-day timetable management, matching, session updates, exceptions, closures, leave, calendar feeds.
- `viewer`
  Read-only operational visibility.

## Local PostgreSQL

```powershell
docker compose up -d postgres
cd backend
py -m alembic upgrade head
```

## Legacy Data Import

```powershell
cd backend
py -m app.import_legacy_sqlite .\timetabling.db
```

Run this only after PostgreSQL is configured and migrations have been applied.
