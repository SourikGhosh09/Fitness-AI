# Operations Runbook

## API unavailable
Check process/platform health, configuration and database connectivity; do not mutate data while diagnosis is uncertain. Restore last known-good deployment if required.

## Database/migration failure
Stop writes, capture logs/version, verify backup, inspect Alembic current/head, use tested downgrade/restore procedure rather than manual schema edits. Validate integrity before reopening writes.

## Authentication/API failures
Confirm server time/config/token storage and DB availability. Never log bearer secrets. Revoke/rotate compromised credentials.

## Background sync/training failure
Pause worker, preserve queue/provenance, fix root cause, replay idempotently. Never auto-promote an uncertain model; fall back to deterministic rules/shadow mode.

## High errors/performance
Identify endpoint/query, protect availability with bounded limits/rate controls, roll back regressions, then test the fix.

## Recovery
Follow `BACKUP.md`; verify checksums/integrity and quarantine learning artifacts after uncertain restore until provenance is revalidated.
