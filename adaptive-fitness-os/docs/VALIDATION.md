# Validation report

## Vercel preparation — 2026-09-12

- Added a root FastAPI entrypoint, pinned Python selection, shared requirements, Vercel configuration and upload exclusions. No migration or training loop runs during an API request.
- Targeted backend regression run: **50 passed**, covering hosting safeguards, survey synchronization/training and core API behavior. Seven hosting cases check missing/SQLite/non-TLS rejection, provider URL normalization and serverless pooling, while preserving local SQLite foreign keys.
- Vercel CLI 59.16.0 reports logged out. No hosted database connection is available; live build/deploy, PostgreSQL runtime and Google Form execution remain unverified. Local bundle size estimates are not a successful Vercel build claim.
- Free testing topology and exact activation steps are documented in VERCEL_DEPLOYMENT.md. No paid resource or cloud training worker was created.

Date: 2026-09-10. This report describes local checks, not a production certification.

- Backend baseline: 27 automated cases covering goal validation, fail-closed catalog, noisy adaptation, idempotency/conflicts, pain pauses, restriction handling, key hash/scope/expiry/revocation, cross-user access, complete-once XP, substitution, cascaded deletion, nutrition opt-in, source-review preservation, media/path safety, disabled integrations, stale readiness, readiness deterioration and incomplete-session exclusion.
- Alembic initial migration: executed successfully against SQLite.
- Dataset: imported 1,324 records and 2,648 media references; zero media files downloaded. Byte-level source verification passed.
- Mobile: TypeScript strict check passed; Expo dependency compatibility check passed; Android and iOS JavaScript/Hermes bundles exported successfully.
- PostgreSQL DDL: compiled from metadata; PostgreSQL migration/import is configured as a CI job, not executed locally.
- No native APK/IPA build, device execution, screen-reader audit, offline device race test, cloud deployment, external LLM call, camera evaluation, wearable connection, clinical evaluation, load test, penetration test, or restore drill was performed.
- Two dependency deprecation warnings were emitted by the backend test client's httpx/AnyIO integration. Tests passed; the framework test harness will need updating when those compatibility paths are removed.

See PRODUCTION.md for remaining release gates. All shipping claims should preserve these limits.

## Animated tutorial update

Added backend cases for exact GIF/poster mapping, default reference-only behavior, authorization, missing exercises, expiry/revocation, source-path/commit changes, preserved current grants, input evidence and malicious path rejection. Original dataset paths were checked for all 1,324 records. No real media license was asserted in testing; synthetic grants are isolated test fixtures. Native GIF playback has not been device-tested.

Current combined suite: **41 passed**. TypeScript strict checking and Android/iOS bundle exports passed after the tutorial update. Migration 0002 and reimport completed against the development SQLite database.

## Uploaded media and enabled in-app playback — current delivery

- Owner-uploaded archive verified: 1,324 animated GIFs plus 1,324 thumbnails, all matched to source records and recorded by file hash. The archive JSON matches the pinned dataset byte for byte.
- Complete backend suite: **48 passed**. This includes actual GIF bytes, correct content type, authentication/scope checks, revocation after descriptor retrieval, missing/tampered files, non-expiring owner authorization and idempotent setup that cannot undo revocations.
- Mobile credential tests: **3 passed**, checking trusted API origin, strict asset paths and rejection of external/manipulated destinations.
- TypeScript strict check and Android/iOS bundle exports passed.
- Migrations through 0003 and full setup executed successfully. The owner declaration enabled 2,648 scoped media grants. Repeating setup created zero duplicate grants.
- Six real asset responses (GIF and image for first, middle and last exercises) were tested through the authenticated application API and matched their recorded SHA-256 hashes. The synthetic smoke-test account was deleted afterward.
- Source package includes all supplied tutorial assets. Playback is served from the backend rather than raw GitHub URLs. No native phone/simulator playback test, signed APK/IPA, or cloud deployment was performed.

The reused scratch database failed an integrity check during a follow-up smoke test. Validation was repeated on a fresh database migrated through 0003: full setup, repeat setup, SQLite integrity check, and six authenticated asset requests passed. No scratch database is included in the source archive.

## Neural learning increment — 2026-09-11

- Full backend suite: **58 passed** (48 existing tests plus 10 learning/backup tests). The learning tests cover analytic gradients against finite differences, genuine MLP training on synthetic held-out data, sample collection, consent, no retroactive collection, duplicate ingestion, source validation, owner/scope isolation, CSV review, disjoint splits, future-session evaluation, model deployment/withdrawal, consent changes during training, bounded live adjustments and checksum-verified backup/quarantine restore.
- A further targeted learning-suite run checked that repeated annotation does not compound a downward load adjustment.
- Strict mobile TypeScript check passed; Android and iOS Expo exports passed with the new learning controls. These are JavaScript/Hermes bundles, not APK/IPA builds or native device tests.
- Fresh SQLite migrations through 0004, downgrade to 0003 and re-upgrade passed. Alembic detected no schema drift, and SQLite integrity returned `ok`.
- Fresh full source setup verified/imported 1,324 exercises and all 2,648 authorized media files. Training on this fresh database correctly returned `waiting_for_data`; no user outcomes or synthetic models were seeded into it.
- Synthetic training/backup tests run in isolated temporary databases. Their successful prediction tests demonstrate pipeline operation, not real-world fitness accuracy or clinical benefit. No synthetic test weights or personal databases are in the source package.
- PostgreSQL DDL/OpenAPI regenerated. PostgreSQL runtime migration/backup validation, phone testing, hosted training operations and real-user shadow evaluation remain pending. Existing test-client dependency deprecation warnings remain non-failing.

## Guided contribution increment — 2026-09-12

- Backend: **69 tests passed** (58 existing and 11 contribution cases, including parameterized exclusions). Coverage includes consent, partial data, no invented labels, review translation/idempotency, metadata re-review, ownership, duplicate events/session-exercise pairs, historical context and skipped sets without a fabricated RPE. The contribution suite was rerun after the re-review adjustment.
- Mobile: **8 new tests passed** for form conversion, unknown answers, copied-set feedback reset, numeric/date checks and session-scoped draft persistence/erasure. Storage tests use controlled SQLite/SecureStore substitutes; they do not establish real-device lifecycle behavior.
- Strict TypeScript passed. Android and iOS Expo/Hermes exports passed with the new Contribute tab and input controls. No APK/IPA or device-run claim is made.
- Fresh SQLite migration to 0005, downgrade to 0004 and re-upgrade passed; Alembic reported no schema drift and integrity check returned `ok`. OpenAPI and PostgreSQL DDL regenerated. PostgreSQL runtime migration/restore remains a deployment validation task.
- Training source records were test fixtures only, held in temporary test databases. The deliverable contains no collected participant dataset, private backup, credential or trained user weights.
- Native accessibility/usability, intermittent mobile connectivity, production hosting and public participant onboarding remain to be verified after deployment.

## Initial exercise knowledge training — 2026-09-12

- Real training completed on the supplied exercise dataset: 916 training records, 219 validation records and 189 held-out test records. The vocabulary used training names only; heuristic equipment/position families were separated before splitting. No personal examples, anatomy textbook text or media entered this network.
- Held-out source-label accuracy: **70.9%**, macro F1 over represented classes **0.590**. Nearest-name baseline: **59.8%**. The fixed suggestion gate returned 97 suggestions, 89 matching source labels; 92 held-out names were marked uncertain. This does not demonstrate clinical safety, optimal programming, general language understanding or uniform class quality.
- Full backend suite: **79 passed**. New coverage verifies backpropagation with numerical gradients, source/model checksums, vocabulary isolation and group splits, recomputed held-out metrics, invalid-weight rejection, source-change abstention, category coverage, exact-source precedence, symptom priority, authentication/owner isolation, read-only answers and approved-only goal-priority ordering.
- Strict TypeScript and both Android/iOS Expo/Hermes bundle exports passed with the muscle-detail component, knowledge quick questions and experimental neural explorer. Native phone behavior, screen-reader usability and APK/IPA builds remain unverified.
- Source-only JSON weights, full evaluation report and educational provenance are included. No private database, participant model, signing credential or external-provider key is included. The RPE network still needs consented participant outcomes.
- No schema change was introduced. Current migrations remain at 0005. OpenAPI regenerated. Existing non-failing test-client deprecation warnings remain; PostgreSQL deployment and production security gates are unchanged.


## Google Forms bridge — 2026-09-12

- Full backend suite: **95 passed**, including 16 new survey test cases. Coverage includes signed requests, expiry and replay, idempotent enrollment, ordered response revisions, edits/deletions/withdrawal, history rebuilding, preserved models for ordinary new outcomes, contributor isolation, missing/pain exclusions and re-evaluation after metadata review changes. An end-to-end synthetic survey test produced genuine saved neural weights; tests also confirmed that automatic promotion cannot replace a live model. Existing dependency deprecation warnings remain non-failing.
- Apps Script bridge logic: **5 Node tests passed** with controlled Google-service substitutes. These verify payload semantics, exact HMAC canonicalization, durable retries, revision changes, invalid-edit removal and withdrawal cleanup retries; they do not establish real Google trigger execution.
- Fresh SQLite migrated to 0006, downgraded to 0005 and re-upgraded. Alembic found no schema drift and SQLite integrity returned `ok`. PostgreSQL DDL and OpenAPI regenerated; hosted PostgreSQL execution remains pending.
- Google Forms/Apps Script APIs checked against official documentation. The session has no callable Forms/Apps Script write action, so no native Google Form was created or connected in the user's account. No public backend or scheduled cloud worker was deployed. The package supplies the actual installer and activation procedure.
- No new real-user weights were trained in this increment. New candidate training uses the existing consent-aware RPE learner, with automatic shadow-only promotion; safety rules and live release gates remain independent.
