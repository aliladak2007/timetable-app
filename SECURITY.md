# Security Summary

## Implemented Hardening

- Argon2 password hashing.
- First-run admin bootstrap instead of default credentials.
- JWT access tokens with user `session_version` invalidation support.
- Role-based access control for `admin`, `staff_scheduler`, and `viewer`.
- Login rate limiting.
- Request size limits.
- Reduced CORS surface through environment-controlled origins.
- Disabled Swagger/ReDoc outside development by default.
- Structured audit logging for authentication, user administration, recurring schedule changes, exception changes, and calendar feed creation.
- Tauri desktop shell restricted to launching the packaged backend sidecar.

## Threats Addressed

- Plaintext password storage.
- Unauthenticated access to schedule and student data.
- Overly permissive role handling.
- Silent session persistence after admin revocation.
- Missing audit trail for sensitive changes.
- Public-by-default calendar exposure.
- SQLite as the production database target.

## Residual Risks

- JWTs are currently stored in the frontend session context for the active desktop/web session. They are not persisted as plaintext passwords, but a compromised local user session can still abuse them until expiry or forced logout.
- The desktop bundle does not embed PostgreSQL. Production deployments still need a protected PostgreSQL instance configured for the packaged app.
- Private ICS feed URLs are bearer-style secrets. Anyone holding the token can read that calendar until the token is revoked.
- In-memory login rate limiting is process-local. It is sufficient for a packaged local app and dev, but not equivalent to a distributed edge limiter.

## Operational Requirements

- Use strong unique admin passwords.
- Keep PostgreSQL bound to the expected interface only.
- Rotate calendar feed tokens when staff or device ownership changes.
- Restrict access to the packaged app host and Windows user accounts that can launch it.
- Back up the PostgreSQL database and retain audit logs.
