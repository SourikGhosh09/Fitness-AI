# Honest implementation status

| Requested area | State in this package |
| --- | --- |
| Dataset import, provenance, media mapping | Implemented; 1,324 records; 1,324 uploaded GIFs and thumbnails integrated for authenticated in-app playback using owner authorization |
| Enriched metadata | Extensible review layer; heuristic pattern suggestions; all source records require review |
| Profile / multiple goals | API implemented with total validation; simplified onboarding UI |
| Assessment / capability scores | Quick questionnaire only; guided and automatic estimates not implemented |
| Safety | Deterministic fail-closed core for reported pain, restrictions, metadata and equipment; not medically validated |
| Explainable ranking | Implemented heuristic scoring with saved reasoning |
| Movement model | Initial resistance patterns; comprehensive sport/cardio/mobility model pending |
| Full workout phases | Preparation, training and cooldown instructions; dedicated activation/dynamic mobility/conditioning engines pending |
| Load / RPE / RIR | Implemented initial conservative prescriptions |
| Progression strategies | Small load change after three sessions; other strategies metadata/design only |
| Volume / fatigue / deload | Readiness and workload heuristics; weekly caps, longitudinal fatigue and complete deload logic pending |
| Periodization | Domain/schema foundation; full macro/meso/microcycle programming pending |
| Substitution | Same-pattern reviewed alternative; pain/discomfort pause; pre-logging only |
| Feedback / history | Guided contribution wizard, optional check-ins, actual effort, copy-set controls, unknown answers, enjoyment/duration, private history, draft/retry behavior and operator review; body-composition UI pending |
| Nutrition | Optional approximate macros based on supplied maintenance estimate; trends, hydration and meals pending |
| Wearables | Explicitly unavailable; architecture only |
| Camera | Explicitly unavailable; no permission requested; architecture only |
| Exercise knowledge | Trained source-only 64-unit name classifier, 19 sourced target categories, muscle-function references, goal-priority ordering and read-only explanations; 70.9% held-out source-label accuracy, experimental, not clinically validated |
| LLM | Not connected; bounded rule-based and sourced knowledge answers |
| Personalization ML | Actual 32/16-unit CPU neural network, consent-aware collection, reviewed CSV ingestion, train/evaluate/registry and bounded inference implemented; no real-user-trained or clinically validated model included |
| Google survey bridge | Native Apps Script installer, private links, signed revision-aware synchronization and automatic validation/training/shadow promotion implemented; Google account activation and public backend still required |
| Data/model backups | SQLite snapshot/verified quarantine restore implemented and tested; hosted PostgreSQL backup/PITR and encryption configuration pending |
| Gamification | One-time XP, levels, recovery reward; avatars/base/challenges pending |
| Mobile | Expo source, type checking, bundle validation; no device-tested signed binaries |
| Offline | Persistent cache/outbox + deduplication; native QA and conflict-resolution editor pending |
| Database | Migrated relational core plus JSON snapshots and versioned extension domains; full normalization evolution pending |
| Auth / API keys | Implemented scopes, hashed secrets, expiration/revocation and owner isolation |
| API | /api/v1 routes and generated OpenAPI; full response typings and rate limits at distributed ingress pending |
| Security | Argon2, hashed tokens, basic limits, no-store, tests; audit, penetration test and operational hardening pending |
| Accessibility | Native labels, scalable text, large controls and text alternatives; device audit pending |
| Repository / deployment | Target repository exists; source upload rejected by GitHub with HTTP 403; latest package saved locally; not deployed |

These gaps are production blockers or remaining scope, not silently completed features. This delivery is a substantive starting implementation, not the requested complete production-grade fitness operating system.

## Notion collection addition (2026-09-15)

Implemented: native opt-in/status screen, session-authenticated consent API, Notion-to-backend polling, pagination/retries, normalized deduplication, corrections, review gating, model invalidation, withdrawal cleanup queue, migration 0007, Compose worker profile, and restore quarantine.

Not activated: live server-side Notion credential, hosted worker and database, connected real-device test. Native-app-to-Notion export, public Notion respondent form, and automatic approval/promotion are not part of this addition. See integrations/notion/README.md.
