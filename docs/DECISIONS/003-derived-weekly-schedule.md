# ADR 003 — Derive the weekly schedule from existing durable state

**Status:** Accepted  
**Date:** 2026-09-25

## Context
Evolve needs a weekly training/rest view and missed-session replanning, while the project already stores selected weekdays in the profile and durable dated workout snapshots. A second mutable schedule table would create competing truth before periodization requirements are stable.

## Decision
For v0.3.0, compute the current Monday–Sunday week deterministically from profile training days, completed workout snapshots and completed-set history. Persist the assigned `session_template` and `schedule_context` inside each generated workout snapshot. Persist regeneration decisions in `recommendation_decisions`. Do not create a new schedule table yet.

## Alternatives considered
- New weekly schedule/program tables immediately: rejected for now because they duplicate current-week truth and add migration/state-reconciliation complexity.
- Keep every training day full body: rejected because it cannot express the requested frequency/split behavior.

## Consequences
Weekly views can be regenerated without migration, existing Momentum workouts remain readable, and recommendation history stays auditable. Multi-week mesocycle/periodization state may later justify normalized program entities; that will require a new ADR and migration rather than silently changing this model.
