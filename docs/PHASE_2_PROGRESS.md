# Phase 2 development progress

## Increment 1 — adaptive programming core

Status: Increment 1 shipped in Momentum; current session engine is `rules-0.3.0` after the Evolve weekly layer integration.

This increment turns the original three-session load heuristic into a broader, still conservative, adaptive programming loop. It intentionally remains deterministic and auditable; the neural RPE model may annotate or conservatively reduce a prescription only after this rules layer has passed safety checks.

### Implemented

- Goal-aware baseline programming for strength, hypertrophy, muscular-endurance and general training emphasis.
- Explicit rep ranges while retaining a single target-repetition value for backward-compatible logging.
- Three-session double progression: comfortable completion progresses repetitions first; after the top of the range, a small load increase may be proposed.
- Repeated difficult/incomplete sessions can reduce load.
- Readiness bands can hold progression and reduce sets/load/RPE demand.
- Recent completed workouts are aggregated by workout ID so fatigue is not double-counted across exercises.
- Conservative deload trigger when reduced readiness combines with repeated recent difficulty.
- Trailing seven-day primary/secondary set-equivalent accounting.
- Experience-banded set-equivalent guardrail to prevent the planner from continually adding volume to the same primary muscle.
- Every workout now stores a `programming` explanation block and every exercise stores its adjustment action/reason.
- Progress API reports adaptive-engine version, trailing workload and current guardrail.
- Mobile Today/Progress screens surface the adaptive policy, rep range, planned load, RPE/RIR, adjustment reason and workload guardrail when available.

### Safety and interpretation

The set-equivalent caps, readiness thresholds and load changes are engineering heuristics. They are not clinically validated, do not diagnose recovery, and are not asserted to be optimal physiological training doses. Existing pain/red-flag/restriction gates remain authoritative and run before adaptive programming.

### Compatibility

No database migration is required. Existing completed workout JSON remains readable. New history summaries add fields such as workout/day, completed sets, average/minimum reps and muscle metadata; old history lacking these fields falls back conservatively.

### Validation in this uploaded package

- `backend/tests/test_system.py` plus the new Phase 2 suite: 35 passed.
- Backend suite with package assets prepared: 136 passed, 3 deselected. The deselected hosting cases require the optional `psycopg` package, which is not installed in the execution container.
- New Phase 2 tests cover rep-before-load progression, top-of-range load progression, difficult-session regression, missing-effort handling, fatigue/deload detection, trailing workload math, plan explanation fields and reduced-readiness scaling.
- Mobile TypeScript validation could not be completed in the execution container because the project dependencies were not fully installable there. The UI edits are deliberately limited to rendering optional fields already returned by the backend.

## Next Phase 2 increments

1. ~~Program split/frequency logic based on actual training days instead of the current fixed movement-pattern loop.~~ **Completed in Evolve v0.3.0.**
2. Exercise-specific progression modes for bodyweight, machines, dumbbells and unilateral work, including available load increments.
3. Mesocycle state: accumulation, intensification, deload and reset with explicit cycle history.
4. Cardio, mobility and conditioning dose allocation as first-class programming domains.
5. Better assessment-derived capability baselines and exercise-specific starting loads.
6. Native device/offline reconciliation testing and a clearer adaptation timeline UI.
7. Longitudinal evaluation of the deterministic policy before allowing broader learned personalization.

## Increment 2 — Evolve weekly programming

Status: implemented in **v0.3.0 — Evolve** with `rules-0.3.0` + `weekly-0.3.0`.

Implemented: derived Monday–Sunday plans from selected training days; frequency-aware Full Body/Upper/Lower templates; tracked missed-session carry-forward without silently consuming the sequence; first-observed-week protection against fabricated misses; day-specific pattern delegation to the existing safe session engine; completed-history muscle recency/set-equivalent snapshot; `/workouts/week`; profile/onboarding day picker; Plan timeline UI; session-template titles/carry-over reasons; pre-logging whole-session regeneration for variety/equipment/time/fatigue; versioned recommendation decisions and regression tests. No database migration was required.

Validation: the Evolve/Phase 2/System focused suite passes 44 tests. The prepared full backend suite passes 142 tests; 3 hosting-only cases fail in this execution container because the optional `psycopg` driver is not installed. Mobile dependencies are not installed in this package environment, so a complete Expo typecheck/native-device run remains an explicit release gate.
