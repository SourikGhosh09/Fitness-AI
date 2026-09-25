# Fitness AI Implementation Roadmap

## Current milestone — v0.2.0 Momentum / Phase 2
- [x] P2-001 — Readiness-aware prescription scaling and explainable adaptation.
- [x] P2-002 — Rep-range/double-progression foundation.
- [x] P2-003 — Fatigue/deload and trailing workload awareness.
- [x] P2-004 — Momentum UI foundation and adaptive prescription presentation.
- [ ] P2-005 — Schedule-aware weekly split/frequency planner.
  - Depends on: P2-001..004
  - References: `docs/PRD.md`, `docs/FEATURES.md`, `docs/ARCHITECTURE.md`
  - Acceptance: training days/rest days respect availability, goals, recovery and recent workload; decisions are explainable; missed sessions can be safely replanned.
  - Tests: planner unit tests, API integration tests, mobile state tests.
- [ ] P2-006 — Longitudinal muscle-volume targets and progression constraints.
- [ ] P2-007 — Full cardio/mobility/conditioning allocation.
- [ ] P2-008 — Capability assessment and confidence/provenance.
- [ ] P2-009 — Native-device offline/accessibility validation.
- [ ] P2-010 — Hosted PostgreSQL/deployment validation and operational hardening.

## Later
- [ ] P3-001 — Optional native health/wearable adapters.
- [ ] P3-002 — Opt-in evaluated camera pipeline.
- [ ] P3-003 — Narrow provider-backed conversational intent adapter.

Production release remains gated by `docs/PRODUCTION.md`.
