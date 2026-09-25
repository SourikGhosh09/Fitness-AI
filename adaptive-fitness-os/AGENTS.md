# AI Agent Instructions — Fitness AI

## Source of truth
This is the active Adaptive Fitness OS implementation. Read `README.md`, `docs/PRD.md`, `docs/FEATURE_STATUS.md`, `docs/PHASE_2_PROGRESS.md`, `TASKS.md`, `HANDOVER.md`, and relevant specifications before changing code. The parent repository contains legacy duplicates; do not implement new work there unless explicitly migrating it.

## Mandatory change protocol
For every meaningful implementation change: update tests, `CHANGELOG.md`, `HANDOVER.md`, `TASKS.md`, and every affected permanent specification. Architecture decisions belong in `docs/DECISIONS/`, not HANDOVER. Keep claims evidence-based; never mark device/cloud/clinical validation complete without performing it. Preserve fail-closed safety, owner isolation, consent, immutable history, deterministic fallbacks, and auditable recommendation reasoning.

## Engineering rules
Use typed validation and authenticated owner-derived IDs. Never bypass safety for ML/coach/UI convenience. Never commit credentials. Database changes require Alembic migrations and downgrade/upgrade validation. API changes require API spec/OpenAPI updates. UI changes require UI spec and accessibility consideration. New adaptive behavior requires deterministic tests including edge/failure cases. Prefer small reversible changes and preserve backward compatibility where practical.

## Before finishing a task
Run applicable backend/mobile checks, document checks that could not run, cross-check docs against implementation, update current status, and package only after checking for accidental secrets.
