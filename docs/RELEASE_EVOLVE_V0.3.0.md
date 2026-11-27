# Fitness AI v0.3.0 — Evolve

## Release goal
Make the **training week** adaptive, not only the individual workout.

## Added
- Deterministic weekly planner `weekly-0.3.0`.
- Frequency-aware session templates driven by the profile's selected weekdays.
- Missed-session carry-forward after tracking begins; first-week protection against invented misses.
- Day-specific pattern intent passed to `rules-0.3.0` session generation.
- Derived completed-history muscle recovery-recency snapshot.
- `GET /api/v1/workouts/week`.
- Safe pre-logging whole-session regeneration (`variety`, `equipment`, `time`, `fatigue`).
- Plan timeline, Evolve release identity, session-template titles and editable schedule controls in mobile UI.

## Safety/interpretation
Weekly split and recovery labels are conservative engineering heuristics, not validated medical/physiological recovery measurements. Existing pain/red-flag/restriction, approved-metadata, equipment, readiness and workload gates remain authoritative. Regeneration cannot rewrite a started workout.

## Data model
No migration. The week is derived from existing profile/workout/history state. Generated workouts store `session_template` and `schedule_context`; regeneration increments workout version and records a decision.

## Validation
- Focused Evolve + Phase 2 + system suites: 45 passed.
- Prepared full backend suite: 146 passed; 3 hosting-only failures because the execution container does not have optional `psycopg`.
- Mobile source parses past the edited JSX with global TypeScript, but complete project typecheck cannot run without installed React/Expo dependencies; native device validation remains open.

## Next
P2-006 longitudinal muscle-volume targets and progression constraints, followed by explicit mesocycle/periodization state.
