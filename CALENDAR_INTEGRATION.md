# Calendar Integration

## Supported Workflows

- Teacher ICS export.
- Student ICS export.
- Centre-wide private feed token generation.
- Session CSV export for downstream reporting.

## How It Works

- Manual ICS exports are authenticated API downloads.
- Feed-style calendar subscriptions use revocable private tokens stored server-side as hashes.
- The packaged app keeps calendar features optional. If feed creation or external sync is not configured, the core scheduling workflow still works.

## Security Notes

- Never publish private feed URLs publicly.
- Treat ICS feed tokens like passwords.
- Revoke and recreate feed tokens when a device is lost or staff access changes.
- Direct phone subscription requires the backend to be reachable from the subscribing device. For many users, manual ICS import will be the practical minimum viable workflow.

## Current Limitations

- Google Calendar direct OAuth sync is not implemented yet.
- Outlook / Microsoft 365 direct sync is not implemented yet.
- The packaged desktop app can generate exports locally, but phone subscription feeds require network reachability to the backend.
