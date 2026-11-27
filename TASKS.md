# Fitness AI Implementation Roadmap

## Current milestone — v0.3.1 Evolve / Phase 2
- [x] P2-001 — Readiness-aware prescription scaling and explainable adaptation.
- [x] P2-002 — Rep-range/double-progression foundation.
- [x] P2-003 — Fatigue/deload and trailing workload awareness.
- [x] P2-004 — Momentum UI foundation and adaptive prescription presentation.
- [x] P2-005 — Schedule-aware weekly split/frequency planner.
  - Depends on: P2-001..004
  - References: `docs/PRD.md`, `docs/FEATURES.md`, `docs/ARCHITECTURE.md`
  - Acceptance: training/rest days respect availability; tracked misses carry forward; day intent is explainable; Today delegates only supported patterns.
  - Tests: planner unit tests and API integration tests implemented; native mobile state/device validation remains under P2-009.
- [x] P2-005A — Safe pre-logging whole-session regeneration with decision/version audit.
- [ ] P2-006 — Longitudinal muscle-volume targets and progression constraints.
- [ ] P2-007 — Full cardio/mobility/conditioning allocation.
- [ ] P2-008 — Capability assessment and confidence/provenance.
- [ ] P2-009 — Native-device offline/accessibility validation.
- [ ] P2-010 — Hosted PostgreSQL/deployment validation and operational hardening.

### Release hygiene
- [x] REL-031 — Make the authoritative application the release ZIP root and remove duplicate legacy tree
  - Acceptance: `CHANGELOG.md`, `HANDOVER.md`, `TASKS.md`, `AGENTS.md`, `README.md`, `SECURITY.md`, and `docs/` are directly visible from the extracted project root.
  - Validation: packaging script/check confirms current version in CHANGELOG and HANDOVER and rejects duplicate nested source roots.


## Later
- [ ] P3-001 — Optional native health/wearable adapters.
- [ ] P3-002 — Opt-in evaluated camera pipeline.
- [ ] P3-003 — Narrow provider-backed conversational intent adapter.

Production release remains gated by `docs/PRODUCTION.md`.
