# Fitness AI — Phase 2 handover

## Source-of-truth discovery

This repository currently contains two application trees:

- top-level `backend/`, `apps/`, `docs/` — older foundation
- `adaptive-fitness-os/` — newer implementation with neural RPE learning, contribution flow, Notion sync, exercise knowledge and sequencing

The Windows launchers already prefer `adaptive-fitness-os/` when it exists. Phase 2 development in this package therefore continues in **`adaptive-fitness-os/`** to avoid splitting new behavior across two generations of the app.

A later cleanup should remove or archive the older duplicate only after checking deployment paths and preserving any files that exist only at the root.

## Phase 2 increment implemented

Engine version: `rules-0.2.0`

Changed areas:

- `adaptive-fitness-os/backend/fitness/engine.py`
- `adaptive-fitness-os/backend/fitness/api.py`
- `adaptive-fitness-os/backend/tests/test_phase2_adaptive_programming.py`
- `adaptive-fitness-os/apps/mobile/App.tsx`
- `adaptive-fitness-os/docs/FEATURE_STATUS.md`
- `adaptive-fitness-os/docs/PHASE_2_PROGRESS.md`

The increment adds goal-aware rep ranges, rep-before-load double progression, readiness scaling, recent-difficulty fatigue aggregation, conservative deload behavior, trailing seven-day set-equivalent workload guardrails, richer history summaries and visible explanations in the mobile UI.

## Validation

Backend: 136 tests passed with package assets prepared; 3 optional PostgreSQL hosting tests were deselected because `psycopg` is not installed in the execution environment. The focused original-system + Phase 2 suite reports 35 passing tests.

Mobile dependency installation could not be completed in the execution environment, so the TypeScript build is **not claimed as validated** for this delivery. Backend behavior and contracts are the validated part of this increment.

## Recommended next task

Continue Phase 2 with schedule-aware split/frequency programming and equipment-specific load increments, then add mesocycle state after those behaviors are covered by regression tests.
