# Fitness AI Handover

## Current state
Current development release is **v0.3.1 — Evolve**. The distributed ZIP now opens directly at the authoritative application root; the older duplicated parent application tree is no longer included in the release package.

## Recently completed
The v0.3.1 patch corrected the release-package structure: maintained control files are visible at the project root, legacy duplicate application files are excluded, and release metadata is synchronized. Packaging validation now checks that `CHANGELOG.md` and `HANDOVER.md` both identify the current release. No training-policy behavior changed; `rules-0.3.0` and `weekly-0.3.0` remain intentional.

Evolve added `backend/fitness/weekly.py`, `weekly-0.3.0`, and upgraded the session engine to `rules-0.3.0`. The app now derives a Monday–Sunday plan from selected training days and durable history, assigns frequency-aware session templates, carries tracked missed sequence slots forward, protects brand-new users from fabricated misses, exposes completed-history recovery recency, and feeds the assigned movement-pattern intent into Today generation. The mobile Plan screen renders the week; onboarding/Profile can edit training days. Active unstarted workouts can be regenerated for bounded reasons, with workout versioning and recommendation-decision audit.

## Workout logbook (added after v0.3.1)
`backend/fitness/logbook.py` + `workout_logs` table (migration 0008) hold a free-form dated journal, one entry per owner and local date, separate from the engine's immutable `performance_logs`. The mobile Log tab is `apps/mobile/src/WorkoutLog.tsx` with pure helpers in `workout-log.ts` (`npm run test:log`). Timers are clock-based (stored epoch seconds), so backgrounding does not drift them; no OS notification is scheduled when the app is closed. Tutorials reuse `ExerciseTutorial` (new `autoStart` prop) for exercises that carry a catalog `exercise_id`; custom exercises have none. Not yet validated on a physical device.

## Validation
Focused Evolve + Phase 2 + system tests: **45 passed**. Prepared full backend suite: **146 passed, 3 environment failures** because the optional PostgreSQL `psycopg` driver is not installed in this execution container. The source ZIP does not include installed mobile `node_modules`, so complete Expo/React Native typecheck/native-device validation is still open.

## Current work / immediate next step
Proceed to P2-006: longitudinal muscle-volume targets/progression constraints, then mesocycle/periodization state. Before that, run `npm ci`, `npm run typecheck`, mobile tests and a physical Android smoke test for Plan/Today/Profile schedule changes and offline cache behavior.

## Known limitations
Weekly recovery labels are recency heuristics, not biological/medical recovery measurements. The weekly schedule is derived current-week state, not a full mesocycle calendar. Cardio/mobility are not yet first-class scheduled domains. Hosted PostgreSQL, signed native builds, wearables/camera and production validation remain incomplete.

## Files currently central to Evolve
`backend/fitness/weekly.py`, `backend/fitness/engine.py`, `backend/fitness/api.py`, `backend/fitness/contracts.py`, `backend/tests/test_evolve_weekly_programming.py`, `backend/tests/test_system.py`, `apps/mobile/App.tsx`, plus the maintained docs.

## Instructions for next AI session
Read `AGENTS.md` and `PROJECT_FILE_MAINTENANCE_INSTRUCTIONS.txt`. Preserve deterministic safety and derived-schedule rules. Update `HANDOVER.md`, `CHANGELOG.md`, `TASKS.md` and all affected permanent specs with each meaningful change. Move permanent architecture choices into `docs/DECISIONS/` rather than accumulating them here.
