# Technical design

## Stack decision

React Native/Expo gives one TypeScript UI across Android/iOS and access to native SQLite and secure credential storage. FastAPI supplies request validation and OpenAPI; PostgreSQL is the deployment database; SQLite supports local development. The native health and camera components need development builds and their own platform adapters. Current pinned mobile baseline: Expo 54, React Native 0.81.5. See the [Expo SDK documentation](https://docs.expo.dev/versions/v54.0.0/) and [SQLite documentation](https://docs.expo.dev/versions/v54.0.0/sdk/sqlite/).

## Three decision layers

```mermaid
flowchart TD
  U["Mobile or API client"] --> A["Authenticated application services"]
  L["Optional LLM intent adapter"] --> A
  A --> S["Hard safety filters"]
  S --> R["Explainable candidate ranking"]
  R --> P["Validated plan and provenance"]
  P --> D["Transactional database"]
  D --> H["Completed session history"]
  H --> R
```

Implemented: deterministic rules, explainable weighted ranking, and a trainable neural RPE prediction subsystem. No model trained on real users is included; the external LLM remains unimplemented. The coach endpoint identifies itself as rule-based and returns no fabricated actions. The intended LLM layer can select typed application tools; it cannot write SQL, select a user ID, skip safety, invent progress or return authoritative unsaved workouts.

## Request processing

Authenticate an opaque token → enforce scope → resolve owner from token → validate request → enforce workout state and safety → transact mutation and decision record → return response. Owner IDs supplied by clients are never accepted for resource authorization. Key hashes are indexed. Transactions protect goals, plans, logs, XP and account deletion. PostgreSQL row locks serialize plan creation/completion per owner or workout.

Current plan creation uses local profile timezone and an owner/day uniqueness constraint. Day changes do not invalidate historical records. Past prescriptions are immutable JSON snapshots for audit; model response is computed from completed historical workout logs.

## Ranking and adaptation

Candidates without approved metadata are excluded. Equipment, blocked patterns, skill, preferences and restrictions are evaluated before scores. Weighted goal fit, compatibility and historical adherence add score; fatigue penalizes score. These weights are implementation heuristics, not validated physiological estimates. Three distinct completed sessions are needed before the initial 2.5% increase or 10% reduction rule. This rule is intentionally limited and does not constitute a complete deload/periodization model.

Workload calculation has direct and half-weight secondary contributions with overlap deduplication. The result is an explicitly labeled heuristic; it is not yet a weekly constraint in the planner. The planner currently programs resistance patterns; weighted cardio/mobility preferences do not yet produce a full concurrent program.

## Offline protocol

Persist each set before attempting transmission. Client-generated UUID is stable throughout retry. The server enforces owner/event uniqueness and workout/exercise/set uniqueness. Same event/same body returns its previous result; changed body returns 409. Retain unresolved conflicts in the outbox. Persist session snapshot and English instructions. Tutorial GIFs are now served from supplied local files after an authenticated rights check. The player attaches credentials only to validated application-relative routes; no third-party media host receives account credentials. Native media caching remains disabled. Reject expired credentials for remote reads; permit local draft logging without inventing refreshed credentials.

Pending limitations: full reconciliation UI, local at-rest database encryption, account-switch replay tests, stale-plan revalidation across offline state changes and native device tests. SQLite outbox behavior is implemented but not device-validated.

## Future adapters

Wearable measurements: provider ID, external event ID, consent version, start/end timestamps, unit, original value, normalized value, quality and source priority. Deduplicate provider/event IDs; no single HRV/RHR value controls a session. Health tokens remain server-encrypted or OS-protected as appropriate.

Camera: explicit opt-in, permission prompt, on-device frames → pose keypoints → confidence gate → exercise-specific state machine → rep/tempo/ROM signals. Never infer injury or guarantee form safety. Discard frames by default. Low-confidence or unsupported exercise means no coaching cue.

ML: event definitions and provenance must be stable before training. Use temporal/user-separated validation; evaluate subgroup performance and calibration, compare with rules, shadow-mode first, rollback on safety/adherence regressions. No untrained system is described as learning.

## Scientific policy grounding

Progressive resistance training should account for experience, goals and context; the [ACSM progression position stand](https://pubmed.ncbi.nlm.nih.gov/19204579/) is a foundational reference, not validation of this implementation. Calorie requirements are estimates requiring individual context and monitoring; see [NIDDK's Body Weight Planner](https://www.niddk.nih.gov/bwp). Current scoring weights and thresholds still require review and evaluation.

## Implemented neural subsystem

`fitness/neural.py` implements a NumPy MLP with 24 inputs (12 numeric features plus 12 movement-pattern indicators), 32/16 tanh hidden units and a scalar RPE regression output. Training uses analytic backpropagation, Adam, training-only normalization, deterministic seeds and validation early stopping. JSON numeric arrays are stored in `learning_models.artifact`; pickle and remote executable models are not loaded. Finite differences verify analytic gradients in tests.

`learning_consent`, `learning_examples`, `learning_models`, `learning_members` and `learning_deployment` are introduced by migration 0004. Snapshots retain pre-prescription features; completed sets add immutable outcomes only with an unchanged consent grant. The trainer uses user-disjoint holdouts plus future sessions of training users. Small single-user experiments use chronological session splits and cannot pass shared deployment gates. Model membership covers training AND evaluation users.

The API exposes only current-user status, session-authenticated consent and train-scoped data ingestion. CSV review, training, activation and rollback are operator CLI actions with server/database access. Imported records wait for review. User API keys cannot train or promote global models. Inference occurs only after deterministic eligibility and programming; it either annotates shadow predictions or applies an explicitly reviewed downward load adjustment, followed by safety validation. See TRAINING.md for exact bounds, metrics, source limitations, privacy behavior and recurring worker operation.

Backup covers database-resident weights and provenance. SQLite restore disables old credentials and quarantines learning. Hosted PostgreSQL backup/PITR, encryption, broader model bias audits and coordinated poisoning defenses remain deployment/release work.

## Human contribution service (migration 0005)

`user_contributions` stores owner-scoped, immutable source submissions, a consent grant, stable event/session IDs, exercise FK, reported time, original answers, frozen previous-history context, completeness report and reviewer provenance. User/event and user/session/exercise uniqueness protect retries. Owner/time indexes support retrieval. Optional observed fields remain null.

`POST /api/v1/contributions` validates the bounded typed contract and checks train scope/consent. `GET /api/v1/contributions` lists only the authenticated owner's latest records with bounded pagination. `fitness.collect` implements the private operator report/show/review/export workflow. Only eligible reviewed sets create existing `learning_examples` records; the established neural trainer and deployment gates remain authoritative.

The mobile Contribute wizard stores versioned per-account drafts. Its mutation requests bind to the opening session, and cache writes are serialized with clear. The cached contributor identity includes a session fingerprint (not the session secret) for safe offline recovery. Retried submissions retain their exact payload and event ID. Unit tests cover source conversion, session-bound draft persistence/erasure, API isolation, source review, unknowns, deduplication and snapshot chronology. Native rendering and real-device offline lifecycle QA remain pending.
