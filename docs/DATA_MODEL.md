# Data Model

The executable SQLAlchemy metadata and Alembic migrations are authoritative; `SCHEMA.md` and generated PostgreSQL DDL provide detailed schema views. Core domains are users/auth sessions/API keys, profiles/goals, exercises/review metadata, readiness, workouts/plans, immutable set logs, decisions/audit, contributions/consent/learning examples/models/deployment, nutrition targets and integration state.

Rules: owner-scoped resources use authenticated user IDs; event IDs provide idempotency; workout prescriptions are retained as snapshots; learning examples retain consent grant provenance; secrets are hashed or externally protected; schema changes require migrations plus upgrade/downgrade tests.

Evolve weekly planning reuses durable profile/workout/readiness/history state and does **not** add a new schedule table. The computed week is derived from `profiles.data.days` plus `workouts.day/status/plan`. New workout snapshots may contain `session_template` and `schedule_context`; recommendation decisions capture regeneration events. Introduce normalized schedule/program entities later only if durable multi-week cycle state cannot be represented without ambiguity.
