# Data Model

The executable SQLAlchemy metadata and Alembic migrations are authoritative; `SCHEMA.md` and generated PostgreSQL DDL provide detailed schema views. Core domains are users/auth sessions/API keys, profiles/goals, exercises/review metadata, readiness, workouts/plans, immutable set logs, decisions/audit, contributions/consent/learning examples/models/deployment, nutrition targets and integration state.

Rules: owner-scoped resources use authenticated user IDs; event IDs provide idempotency; workout prescriptions are retained as snapshots; learning examples retain consent grant provenance; secrets are hashed or externally protected; schema changes require migrations plus upgrade/downgrade tests.

Phase 2 weekly planning should reuse durable workout/readiness/history state and introduce new normalized schedule/program entities only when session snapshots cannot represent the requirement without ambiguity.
