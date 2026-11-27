# Changelog

## Unreleased

### Added
- Workout logbook: dated per-set journal (`workout_logs`, migration 0008) with `GET/PUT/DELETE /logs/{date}`, `GET /logs?start&end`, `POST /logs/{date}/from-plan`, optimistic versioning, previous-performance hints and weekly summaries.
- Mobile **Log** tab: Monday-Sunday date strip and jump-to-date, per-set weight/reps/RIR, session stopwatch with pause, clock-based rest timer, timed-set countdown, warm-up/stretch/cooldown checklists, conditioning, review fields, share-as-text, on-device draft with retry, and each catalog exercise's animated tutorial inline.
- `npm run test:log` and logbook API tests.
### Changed
### Fixed
### Removed
### Security
- The logbook is owner-scoped, `train`/`read` scoped, bounded, and never feeds the adaptive engine, immutable `performance_logs`, XP or learning data.

## 0.3.1 — Evolve

### Changed
- Repackaged the repository so the active `adaptive-fitness-os` application is the ZIP project root instead of being nested behind an older duplicate tree.
- Promoted the maintained development-control files (`CHANGELOG.md`, `HANDOVER.md`, `TASKS.md`, `AGENTS.md`, `README.md`, `SECURITY.md`, and `docs/`) to the immediately visible authoritative project root.
- Bumped application/package/API release metadata to v0.3.1. The training policy remains `rules-0.3.0` and weekly planner remains `weekly-0.3.0` because this patch does not alter programming logic.
- Added packaging validation requirements that verify the current release appears in both `CHANGELOG.md` and `HANDOVER.md` before distribution.

### Fixed
- Removed release-package ambiguity caused by shipping an older application copy alongside the authoritative implementation.
- Removed the confusing parent-level legacy `PHASE_2_HANDOVER.md` from the distributed project layout by packaging only the active source-of-truth project.

## 0.3.0 — Evolve

### Added
- Schedule-aware derived weekly planner (`weekly-0.3.0`) with frequency templates and seven-day status view.
- Tracked missed-session carry-forward and first-observed-week protection against fabricated misses.
- Completed-history muscle recency/set-equivalent recovery snapshot.
- `GET /api/v1/workouts/week`.
- Pre-logging whole-session regeneration for variety/equipment/time/fatigue with versioned decision audit.
- Mobile weekly Plan timeline and editable training-day picker in onboarding/Profile.
- Evolve weekly unit/API regression tests and release documentation.

### Changed
- Session engine version to `rules-0.3.0`; Today generation now receives a weekly session template and movement-pattern intent.
- Momentum UI release labels updated to Evolve v0.3.0.
- Maintained project-control/specification set synchronized with implementation.

### Security
- Regeneration remains owner-scoped, safety-filtered, and is blocked after set logging begins.

## 0.2.0 — Momentum
- Phase 2 adaptive programming increment and Momentum UI foundation. See `docs/RELEASE_MOMENTUM_V0.2.0.md`.
