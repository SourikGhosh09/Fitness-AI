# Fitness AI Handover

## Current state
Current release remains **v0.2.0 — Momentum**. Adding this maintenance pack is documentation/control maintenance only and is explicitly **not a new application version**. The active implementation is this `adaptive-fitness-os/` directory; older duplicated application files exist in the parent repository.

## Recently completed
Phase 2 Increment 1 added readiness-aware scaling, rep-range/double progression, fatigue/deload detection, trailing workload awareness and richer adaptive prescription presentation. Momentum established the current dark high-contrast mobile UI direction.

## Current work / next step
Implement schedule-aware weekly split/frequency programming: training/rest-day allocation, recovery-aware rescheduling, muscle frequency and recent workload constraints, while retaining explainable decisions and safety gates.

## Known limitations
Production gates remain open. Native device validation, hosted PostgreSQL validation, wearables/camera, full periodization and full multi-domain programming are incomplete. See `docs/FEATURE_STATUS.md` and `docs/PRODUCTION.md`.

## Instructions for next AI session
Read `AGENTS.md` and `PROJECT_FILE_MAINTENANCE_INSTRUCTIONS.txt`. Update this file after each meaningful session, but move permanent technical decisions into `docs/DECISIONS/`. Update `CHANGELOG.md`, `TASKS.md` and affected specs with every implementation change.
