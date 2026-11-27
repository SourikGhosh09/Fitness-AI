# Notion automatic collection sync — native app

**Implemented and locally tested; not activated on a live host.** Direction:
**private Notion collection → Fitness API database → mobile contribution queue**.
This release does not export native app workouts to Notion or perform two-way edits.
It replaces the need for the Google Forms bridge for this collection path. The older
Google integration remains optional for existing installations.

## What Sourik does once

1. Run the backend and mobile source following the root README. This folder contains
   source, not an APK. Use test records until the application's remaining release gates close.
2. Create an internal Notion connection in the [developer portal](https://www.notion.so/profile/integrations).
   Grant it read/update content access only to **Workout Observations**. Update access is
   used for withdrawal cleanup. Keep the database private.
3. Save the connection's secret on the backend host as `NOTION_TOKEN`, never in a chat,
   source control, mobile app or an `EXPO_PUBLIC_` variable. ChatGPT's Notion connection
   is separate and cannot supply this server credential.
4. Set `NOTION_DATA_SOURCE_ID=f334c7a2-43bc-4663-a74c-55575df24f07` and the same
   `DATABASE_URL` used by the API. Start the worker below. A continuously running
   process, or an external scheduler invoking `--once`, is required. ChatGPT need not stay open.
5. In the app's Settings, each adult participant enables voluntary shared learning,
   then **Notion collection → Allow my Notion answers to be imported**. They give the
   displayed participant code privately to the collection owner. No personal Notion
   account is required for participants. Consent is recorded in their authenticated app account.

The owner can continue interviewing participants and entering rows in Notion. This
worker automates transfer, not survey distribution. A public respondent form has not
been created. Codes such as `P001` and the existing synthetic demo will not import;
use the participant code actually issued by the app. Never enable consent for someone else.

## Server commands

From the project root, install the pinned Python dependencies as in README. With the
virtual environment activated, export the server variables using the host's protected
secret controls, then:

```bash
cd backend
# Fresh installations: imports the bundled catalog and applies all migrations.
python -m fitness.setup
# Existing installations may apply only the new migration:
alembic upgrade head
# Check one complete cycle; prints counts, never tokens or participant answers.
python -m fitness.notion_worker --once
# Continue checking every five minutes; retry transient errors automatically.
python -m fitness.notion_worker --interval-seconds 300
```

For the bundled local PostgreSQL/API Compose stack:

```bash
# Set DATABASE_URL to the Compose service host 'database', not localhost.
docker compose --profile notion up -d --build
```

Use a supervisor/background-worker host for continuous operation. A short-lived
HTTP function is not a place to run this loop. No hosting account was provisioned,
no billing was enabled, and no uptime or free-hosting entitlement is claimed.
The API reads the worker heartbeat from its database; the Notion token belongs only
on the worker. Expose the API over HTTPS for mobile use.

## Enter one row per exercise set

Open [Workout Observations](https://app.notion.com/p/61125e20e841456d84408ce5ae62c451).

Required for import:

- Participant ID: the app-issued code, shared privately.
- Exercise ID: an exact catalog ID; search the exercise in `GET /api/v1/exercises`.
  The name field is for people, not matching. Do not guess IDs from exercise names.
- Session ID: one stable 8–80 character identifier per workout; reuse for all its sets.
- Set number: 1, 2, 3... with no gaps/duplicates within that exercise and session.
- Workout date; Reps (0–200 integer); Load kg (0–600; use a consistent load convention).
- Record type = Participant; Review = Pending.
- Learning consent and Notion sharing consent: record the person's explicit answers.
- Consent version = `notion-import-v1`; Consent captured at = actual consent date/time.

The app grant is authoritative. Checking Notion boxes cannot enroll an account,
reactivate revoked consent, or approve a training example. Unchecking either consent
box on a previously consented linked row, or setting Sync status to Withdrawn, stops that participant's
Notion import and queues cleanup of their known linked rows. New draft rows with unchecked defaults are simply excluded until completed.

Optional: effort/RPE, pain (Unknown is allowed), skipped, original planned reps/load/
target RPE, experience, sleep, energy, soreness, stress, history mode, enjoyment and duration.
Keep session-level context identical across that exercise's rows. Missing values
stay unknown. More complete answers can help review, but never invent an answer.
Submission ID and Revision are not required: the importer derives stable identity
from the participant/session/exercise and compares normalized content itself.

Notion's numeric property descriptions do not enforce bounds; the backend does.
The importer does not read free-text page bodies, names, contacts or medical notes.
The native app reports last check time and imported/correction counts. The Notion
Sync status field is not a delivery acknowledgement; successful delivery is verified
in the app. Editing a row to Excluded or Needs correction excludes its exercise group.

## Test safely

Automated fixtures are isolated from real Notion and participant databases:

```bash
PYTHONPATH=backend pytest backend/tests/test_notion_sync.py -q
cd apps/mobile
npm ci
npm run typecheck
```

For a connected staging test, use a separate Notion database, a disposable adult test
account, and a staging API database. Explicitly opt in on that test account. Enter a
fixture using an actual catalog ID, run `--once`, and inspect its Contribute history.
Run again: no duplicate should appear. Change a numeric answer: its contribution
returns to pending and affected model versions are retired. Change it to an invalid
answer: the old imported contribution is removed, and the app shows a correction count.
Then disable imports in the app: backend imports disappear immediately, and a successful
worker cycle clears/trashes the known source rows. Do not use these synthetic tests
in a production training dataset.

## Review and training are separate

All imported contributions start pending. Synchronization never invokes training,
approves examples or deploys weights. Use existing operator tools after reviewing
source quality and exercise metadata:

```bash
cd backend
python -m fitness.collect report
python -m fitness.collect show CONTRIBUTION_ID
python -m fitness.collect review CONTRIBUTION_ID --reviewer 'Reviewer name' --evidence 'Actual review evidence'
python -m fitness.ml train
# Optional automatic candidate training on already-approved examples:
python -m fitness.ml watch --interval-hours 24
```

Do not run the Google survey validator to approve Notion records. Current RPE model
training gates need sufficient eligible observations and participants (currently
500 rows and 20 users), complete context, reviewed metadata and held-out evaluation.
The bundled exercise-knowledge model is a different model. An additional Notion row
is not, by itself, evidence of neural learning or improved recommendations.

## Failure, ownership and deletion behavior

- Queries paginate fully before applying changes. A failed/partial query imports nothing.
- Repeat cycles compare normalized hashes, preserving IDs and review for unchanged data.
- Corrections invalidate influenced models and derived examples before rebuilding.
- Rows missing from a complete query remove derived imports conservatively. Missing
  visibility is not described as proof that the original Notion record was deleted.
- A known row cannot be reassigned to a different participant. Native app contributions
  are never overwritten by a Notion row with a conflicting session/exercise.
- App opt-out, shared-learning opt-out, and account deletion invalidate stale import
  generations. Re-enabling generates a new code; old source rows cannot resurrect data.
- Remote cleanup has a durable queue that survives account deletion and retries on
  errors. A 404/permission error does not count as successful erasure. Only known linked
  pages can be cleaned automatically; the owner must handle unlinked collection data.
- Cleanup clears editable row properties and moves the page to Notion's trash. It is
  NOT a guarantee of permanent deletion from Notion's version history, free-text page
  bodies, exports or backups. Do not store participant notes outside defined properties.
- Backups include import state and cleanup queues. SQLite restores quarantine these
  tables. Reconcile the current deletion ledger before resuming workers after any restore.

## Verified API references

[Notion connection types and credentials](https://developers.notion.com/)
[Database/data-source API migration](https://developers.notion.com/reference/post-database-query)
[Page updates](https://developers.notion.com/reference/patch-page)

REST adapter pins `Notion-Version: 2025-09-03`, follows data-source query cursors,
restricts requests to api.notion.com, disables redirects, bounds responses and retries
429/transient errors. Real credential/permission checks and real-device testing remain
required on the selected host; local mocked tests do not establish live connectivity.
