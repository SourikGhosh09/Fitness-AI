# Validation report

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
