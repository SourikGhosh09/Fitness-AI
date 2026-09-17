# Adaptive Fitness OS

An implemented development foundation for an adaptive fitness platform, with an Expo Android/iOS client, FastAPI API, SQLAlchemy persistence, deterministic safety/ranking/progression, an auditable dataset importer, and revocable personal API keys.

**Status: development, not production-ready.** This is not the complete system described in the master brief. The implemented core and outstanding work are explicitly tracked in [feature status](docs/FEATURE_STATUS.md). No model trained on real users, native camera coach, wearable integration, deployment, APK, or App Store release is claimed.

## What works

- Account registration/sign-in with Argon2 password hashes and expiring opaque bearer sessions.
- Personal API keys: cryptographically random secrets, shown once, SHA-256 hashes at rest, scopes, expiry, listing and revocation. API keys cannot mint additional keys.
- Profiles, weighted goals totaling 100%, optional sensitive fields, equipment and restrictions.
- Readiness check, fail-closed safety filtering, explainable ranking, session-specific preparation, RPE/RIR prescriptions, small load changes after three sessions, and substitutions.
- Immutable set events with owner isolation, transactional deduplication, pain pauses, session completion and one-time XP.
- Exercise search, English instructions, and dataset GIF tutorial controls in the library and workouts. The supplied GIFs now play through the authenticated backend inside the app, using the owner’s confirmed media authorization. See [animated tutorials](docs/ANIMATED_TUTORIALS.md).
- Mobile SQLite cache/outbox, explicit sync conflict messages, secure session storage, and signed-out cache erasure.
- Optional approximate nutrition targets; rule-based coaching explanations; account export/deletion API.

## Start the backend

Python 3.11+; tested with Python 3.12. From the repository root:

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r backend/requirements.lock
cd backend
python -m fitness.setup
uvicorn fitness.api:app --host 0.0.0.0 --port 8000
```

Local API docs: `http://localhost:8000/docs`. SQLite is used unless `DATABASE_URL` points to PostgreSQL. Use local test data until release gates are closed.

**The import intentionally does not approve exercise metadata.** The library/search and account features work immediately; training generation returns a clear conflict response until compatible exercise metadata has been reviewed. Test fixtures are never seeded into a user database. See [catalog review](docs/CATALOG_REVIEW.md).

## Start the mobile app

```bash
cd apps/mobile
npm ci
```

Create `apps/mobile/.env` from its `.env.example`, using your computer's LAN IP for a physical device (localhost on a phone means the phone itself). Then:

```bash
npx expo start
```

The project targets Expo SDK 54 / React Native 0.81.5 as a pinned development baseline. Native build commands are `npm run android` and `npm run ios`; these require Android SDK/Xcode respectively. EAS preview configuration produces an APK after an authenticated build in your Expo account. No signing credentials are included.

## Automatic Notion collection sync

The native app now has **Settings → Notion collection**. With explicit app consent,
the background worker imports Notion exercise-set records, detects corrections,
prevents duplicates and handles withdrawal cleanup. **Implemented and locally tested;
not activated on a live host.** No Google Form is required for this path. Start with
[Notion setup and testing](integrations/notion/README.md). A server-side Notion token
and running API/database/worker are still required; none is included in the source ZIP.

## Optional legacy Google Form connection

For free personal testing, see [Vercel deployment](docs/VERCEL_DEPLOYMENT.md): Vercel hosts the Python API and tutorials, external PostgreSQL stores user data, and your computer runs candidate training. Deployment configuration is included; no live deployment is claimed.

The [Google Forms setup guide](integrations/google-forms/README.md) includes a native form installer, private participant links, authenticated submission/edit/deletion synchronization and a candidate-training worker. It needs one Google authorization and a publicly hosted HTTPS backend. The integration is implemented and locally tested; no live Google Form or hosted connection has been created. Passing candidates can update shadow evaluation automatically; live workout changes retain the reviewed release gate.

## Collect data from participants

Open the new **Contribute** tab for a three-step workout form: quick check-in, exercise search/set logging, then review and send. It supports unknown answers, saved drafts, duplicate-safe retries and explicit opt-in. Participants need no CSV or exercise IDs. See [the collection guide](docs/COLLECTING_DATA.md) for setup, owner review and connecting other users to your backend.

## Start with trained exercise knowledge

A trained exercise-name neural classifier is now bundled, alongside sourced muscle functions and explicit exercise-order rules. In **Coach**, use the muscle/order quick questions or expand **Explore the trained neural model**. In **Library**, tap **What this exercise targets**. See [initial knowledge and retraining](docs/EXERCISE_KNOWLEDGE.md) for results, limitations and the one-command training procedure.

## Train your own neural network

The app now includes an actual CPU neural network for RPE prediction, opt-in workout-data collection, historical CSV import, training/evaluation, model deployment controls and database/model backups. No ChatGPT or external AI key is needed. Start with [the training guide](docs/TRAINING.md); use [the backup guide](docs/BACKUP.md) for recovery. No real-user-trained model is bundled, and weak candidates remain experimental.

From `backend`, after setup and data collection:

```bash
python -m fitness.ml train
python -m fitness.ml status
# Optional recurring worker; trains candidates without auto-activating them:
python -m fitness.ml watch --interval-hours 24
```

## Your API key

Run the backend, create/sign in to an account, then open **Settings → Create read-only key**. Copy the one-time secret. For train/coach scopes use authenticated `POST /api/v1/api-keys` in the API docs. Details: [API keys](docs/API_KEYS.md).

A key issued by this backend authenticates to **your deployed Fitness OS API**. It does not provide an external provider's AI model or paid inference credits. The app can operate its deterministic core without any provider key.

## Tests

```bash
cd backend
python -m pytest -q
cd ../apps/mobile
npm run test:media
npm run typecheck
npx expo export --platform android --platform ios
```

See [validation report](docs/VALIDATION.md). Bundling is not native device testing.

## Project map

| Path | Contents |
| --- | --- |
| `backend/fitness` | API, typed request validation, schema, deterministic engine, importer, review CLI |
| `backend/alembic` | Versioned migrations with immutable initial schema snapshot |
| `backend/tests` | Safety, authorization, isolation, deduplication and import tests |
| `apps/mobile` | Native mobile UI, secure credentials, SQLite cache/outbox |
| `data/exercises.json` | Unmodified upstream snapshot, 1,324 exercises |
| `data/tutorial-media` | 1,324 uploaded GIFs and 1,324 thumbnails for in-app tutorials |
| `data/media-authorization.json` | Owner declaration and exact supplied archive/data scope |
| `licenses` | Upstream non-media MIT license and media notice |
| `docs` | PRD, TRD, UI/UX specification, schema, feature status, production gates |

## Dataset and media rights

Source: [hasaneyldrm/exercises-dataset](https://github.com/hasaneyldrm/exercises-dataset), commit `7455efae41b330c265e7cd4b78dfa848e7ce5ebd`. Source bytes are verified against their Git blob hash before import. Non-media content is distributed with the original license. The owner-supplied GIFs and thumbnails are included and enabled by setup using their explicit media authorization. Exact asset hashes and original attribution are retained. See [licensing assessment](docs/LICENSING.md).

## GitHub publishing

Target repository: https://github.com/SourikGhosh09/Fitness-AI. It exists, but the connected GitHub app rejected the source upload with HTTP 403. This local package includes the latest changes. From an authenticated local GitHub CLI or Git checkout with write access:

```bash
git init -b main
git add .
git commit -m "Build adaptive fitness development foundation"
git remote add origin https://github.com/SourikGhosh09/Fitness-AI.git
git push -u origin main
```

A source repository being available does not mean the backend has been deployed.

## Render and Notion pilot

See [deployment and activation instructions](docs/RENDER_NOTION_DEPLOYMENT.md). After cloning, run `python scripts/prepare_assets.py` to restore the compressed catalog/model and verified tutorials before setup or tests.
