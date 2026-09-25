# Test Plan

Every adaptive/safety rule requires deterministic unit tests plus API integration coverage. Critical suites cover authentication/owner isolation, goal/profile validation, fail-closed safety, plan generation, adaptation/progression/deload boundaries, substitution, immutable/idempotent logging, offline retry semantics, consent/withdrawal, learning gates, media authorization, account deletion/export and migrations.

Mobile changes require TypeScript checks and focused state/component tests where available; release claims require native-device validation rather than bundle success alone. Database changes require fresh migration, downgrade/re-upgrade, schema drift and integrity checks. Deployment claims require hosted runtime verification.

Definition of done: relevant tests pass; failures/untested environments are documented; specs/tasks/handover/changelog are synchronized; no secrets are introduced; safety/authorization regressions are release blockers.
