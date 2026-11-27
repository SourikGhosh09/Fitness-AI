# API Specification

The generated contract in `openapi.json` is the endpoint-level source of truth. API prefix is `/api/v1`. Authentication uses opaque bearer sessions or scoped API keys where permitted; authorization derives the owner from credentials.

Major groups: authentication/profile/readiness, workout generation/retrieval/completion/substitution, set logging, exercise/library/media/knowledge, coach, contributions, learning consent/status/import, nutrition, integrations, API keys and account export/deletion. Validation errors use typed FastAPI responses; conflicts such as duplicate/inconsistent immutable events use explicit 409 responses.

Any endpoint change must update implementation tests and regenerate/check `openapi.json`. Future weekly-plan endpoints must expose schedule state and explanation without allowing clients to bypass safety or forge historical completion.

## Workout logbook endpoints

Free-form dated journal, one entry per owner and `YYYY-MM-DD` date. It never feeds the adaptive engine, `performance_logs`, XP or learning data. Writes require `train`, reads require `read`; the owner always comes from the credential.

- `GET /logs?start=&end=` returns per-day summaries (`status`, `sets_done`, `sets_total`, `volume_kg`). Both bounds or neither (default: current profile-timezone week); at most 93 days.
- `GET /logs/{date}` returns the entry, its `version`, and `previous` (last completed sets for each catalog exercise). 404 when absent, 422 for a malformed date.
- `PUT /logs/{date}` upserts. Send `version` 0 to create, or the version you loaded; a mismatch returns 409. Unknown fields, out-of-range values and unknown `exercise_id` return 422. Timer data is stored as epoch seconds (`started_at`, `ended_at`, `paused_seconds`, per-set `completed_at`); `rest_seconds` is per exercise or per set.
- `DELETE /logs/{date}` removes the entry.
- `POST /logs/{date}/from-plan` creates an entry from the already-generated planned workout for that date (404 if none, 409 if a log exists).

Entries are included in `GET /account/export` and deleted with the account.

## Evolve v0.3.0 endpoints

### GET `/workouts/week`
Requires `read`. Optional query `day=YYYY-MM-DD` anchors the derived Monday–Sunday week; omitted uses the authenticated profile timezone. Returns `policy`, `engine_version`, `week_start`, `week_end`, seven `days`, `missed_sessions`, `next_session`, `deferred_sessions`, a completed-history `recovery_snapshot`, and current readiness when a fresh readiness record exists. Invalid date input returns 422. The endpoint does not mutate schedule/workout state.

### POST `/workouts/today`
Still requires a fresh readiness check and `train`. In Evolve it first derives the current weekly day template. Training-day plans persist `session_template`, `schedule_context`, `programming.weekly_policy` and engine version. Rest days remain recovery plans and cannot be promoted to training by regeneration.

### POST `/workouts/{workout_id}/regenerate`
Requires `train`. Body: `{ "reason": "variety" | "equipment" | "time" | "fatigue" }`. Allowed only for an owned `planned` training workout before any set log exists. Variety/equipment attempt alternate approved exercises; time uses a shorter temporary session budget; fatigue requests a conservative set/load pass. The weekly session template is retained, all existing safety/catalog/volume rules rerun, workout `version` increments and a decision event is recorded. Returns 409 for started/paused/completed/rest-day/non-regenerable plans.
