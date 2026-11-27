# 004 Workout logbook is a separate journal

Status: accepted for review.

Context: the user wants a free-form, dated, per-set workout log with timers (reference: a weekly browser log page). The existing `performance_logs` are immutable, tied to a generated plan, and drive progression, fatigue and learning.

Decision: add `workout_logs` (one JSON entry per owner and date, optimistic `version`) behind `/api/v1/logs`. It can be seeded from a generated plan but never writes back to `workouts`, `performance_logs`, XP or learning examples. Timers are client features driven by stored epoch seconds. Catalog `exercise_id` links reuse the authenticated tutorial pipeline.

Consequences: users can log anything without weakening fail-closed safety or poisoning adaptive history. Logged values do not change future plans until a deliberate future decision connects them with review.
