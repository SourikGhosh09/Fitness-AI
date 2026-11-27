# Free Vercel testing deployment

Prepared on 2026-09-12. **Not deployed:** no authenticated Vercel account or hosted database is connected in this workspace. No live URL, Google Form connection or APK has been produced. The prepared files are in the downloadable source archive; GitHub write access was previously denied, so importing the old remote repository alone will not include these changes.

## What runs where

| Component | Location | Practical limit |
| --- | --- | --- |
| FastAPI, authentication, workouts, survey ingestion, model inference | Vercel Hobby | Personal, non-commercial use; usage limits apply |
| Exercise GIFs, thumbnails, source classifier | Read-only Python deployment bundle | Served through existing authenticated media endpoints |
| Accounts, consent, responses, workout logs, candidate weights | External PostgreSQL, e.g. Neon Free | Choose the Free plan; monitor storage and compute allowances |
| Survey validation and neural training | Your computer, connected to that same PostgreSQL database | Computer must be on and online; data waits safely while it is off |
| Android/iOS client | Expo development build or separately built native app | Vercel hosts the API; it does not generate an APK |

Vercel officially supports [FastAPI](https://vercel.com/docs/frameworks/backend/fastapi). [Hobby](https://vercel.com/docs/plans/hobby) is restricted to personal, non-commercial use. Standard [Python functions](https://vercel.com/docs/functions/limitations) allow 500 MB uncompressed and Hobby functions have a 300-second maximum. This project's API is configured for 60 seconds; training is not run in requests. [Hobby cron](https://vercel.com/docs/cron-jobs/usage-and-pricing) is limited to daily schedules, so it cannot replace the existing 15-minute worker loop.

The local data directory is approximately 158 MB and the current installed Python environment approximately 164 MB. This is an estimate, not a verified Vercel build size. The largest bundled GIF is under 0.24 MB. Deployment excludes the mobile client, tests, private training exports, databases and credentials. Media stays behind application authorization, rather than being copied to a public CDN folder.

## 1. Create the free database

Create a PostgreSQL project in [Neon](https://neon.com/) and explicitly select **Free**, without enabling paid upgrades. Check its current allowances in your dashboard. Keep this a small test deployment and monitor database size as responses and model versions accumulate. Choose a region close to the Vercel function region (default US East).

Use the database's **pooled connection string** for Vercel. Keep the provider's TLS parameters. Both `postgresql://` and `postgresql+psycopg://` are accepted; the application normalizes the driver automatically. Do not paste database passwords in chat, commit them, or put them in an `EXPO_PUBLIC_` variable.

For migrations and the local training worker, use the provider's direct connection string. The same database must be used by the API and worker. Create a separate test database for previews; do not let unreviewed preview code access participant production data.

## 2. Initialize once from your computer

Extract the latest source archive. From its `adaptive-fitness-os` directory:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.lock
```

Set `DATABASE_URL` privately to the direct PostgreSQL connection string. On Bash, this avoids putting the value in shell history:

```bash
read -rsp 'Direct PostgreSQL URL: ' DATABASE_URL
export DATABASE_URL
cd backend
python -m fitness.setup
cd ..
```

On PowerShell, use your operating system's secret manager or a private process environment setting instead of the Bash `read` command. Setup applies Alembic migrations and imports the authorized exercises/media references. Run it once per database and again for schema updates, with a backup before updates. **Do not put setup in Vercel's build command or run it at every request.** Safety metadata still requires catalog review before workouts can be generated; see [catalog review](CATALOG_REVIEW.md).

## 3. Link Vercel and configure secrets

From the repository root, install/run the CLI:

```bash
npx vercel@59.16.0 login
npx vercel@59.16.0 whoami
npx vercel@59.16.0 link
```

Select your personal Hobby account and create/select `fitness-ai-api`. Root Directory must be the **repository root**, not `backend` or `apps/mobile`. Framework is **FastAPI**. Leave build, install and output overrides unset; the root `requirements.txt` references the tested lock and `app.py` exports the API. Do not enable a Pro trial or purchase integrations.

In Vercel Project Settings → Environment Variables, configure separately for Production and Preview:

| Variable | Value |
| --- | --- |
| `DATABASE_URL` | Pooled PostgreSQL URL with `sslmode=require` or stronger TLS; separate database per environment |
| `CORS_ORIGINS` | Exact browser frontend origins, comma-separated, if needed; empty for native-only use |
| `SURVEY_FORM_ID` | ID printed by the Google Form installer's `createSurvey()`; optional until connecting Forms |
| `SURVEY_WEBHOOK_SECRET` | Random secret of at least 32 characters; same value in Apps Script; optional until connecting Forms |

The platform sets `VERCEL=1`. The application then rejects missing database configuration, SQLite, and PostgreSQL URLs without explicit TLS. It uses `NullPool` so the provider's pooled endpoint controls connections. Do not set `FITNESS_DATA_DIR=/data` on Vercel: that path is specific to Docker. Vercel uses the bundled repository data automatically.

Generate the webhook secret with your password manager and paste it directly into Vercel and Apps Script properties. Never put it into Google Form questions or mobile configuration.

## 4. Preview, then publish

```bash
npx vercel@59.16.0 deploy
```

Use the actual preview URL printed by the CLI. Preserve preview deployment protection. Use `vercel curl` for protected preview checks, or your authenticated Vercel browser session. Do not use the preview URL as the Google Form's permanent endpoint.

Check `/healthz` and `/docs`; health checks database connectivity, not migration/catalog completeness. Register a fictional test account, sign in, search the exercise library and play a tutorial. Exercise generation should remain blocked until suitable catalog metadata has been reviewed. The existing test suite checks that this gate cannot be bypassed.

When preview checks pass and the Production database is initialized:

```bash
npx vercel@59.16.0 deploy --prod
```

Use the stable production domain printed by Vercel. Verify `/healthz` returns HTTP 200 from an unauthenticated client and `/docs` opens. Native clients and Google Forms must be able to reach this production origin; keep application authentication and signed survey requests enabled. If Vercel account-level protection blocks production, resolve the deployment-access configuration before connecting clients. Do not remove preview protection.

There is no browser fitness frontend in this deployment; `/docs` is the API test interface. For the app, set `EXPO_PUBLIC_API_URL` to the actual production HTTPS origin in `apps/mobile/.env`, then restart Expo or rebuild the native app. Only the public origin belongs in mobile configuration.

## 5. Connect the form and start automatic candidate training

Follow [the Google Forms installer](../integrations/google-forms/README.md). Set Apps Script `API_BASE_URL` to the production origin **without `/api/v1`**, and `WEBHOOK_SECRET` to the matching secret. Run `connect()` and then `createParticipantLink()`; distribute private participant links yourself.

From `backend` on your computer, with `DATABASE_URL` pointing to the same hosted database:

```bash
python -m fitness.survey_worker --interval-seconds 900
```

Keep one worker running. For a single cycle, use `python -m fitness.survey_worker --once`. On a recurring operating-system scheduler, prevent overlapping executions. Do not expose this worker as a public HTTP endpoint or start its infinite loop inside Vercel. Running it every 15 minutes can consume the database's free compute allowance; reduce frequency if needed.

New and edited responses synchronize into PostgreSQL through authenticated requests. The worker validates records, trains eligible candidates and may promote passing candidates to shadow evaluation. A form edit does **not** immediately replace live model weights. Insufficient, withdrawn or invalid data is excluded; reviewed deployment gates remain in force. Existing inference and data collection continue while your computer is off, but validation/training waits for the next worker run.

## 6. Verify and back up before participant collection

Use fictional responses first: submit once, reconcile again (no duplicate), edit a response (revision replaces it), then withdraw consent (learning data removed and affected models retired). Run `showTrainingStatus()` in Apps Script. Small datasets may correctly report insufficient data. Confirm these effects in a test database before collecting real participant records.

The prepared code was tested locally. Actual Vercel build, hosted PostgreSQL runtime, Google authorization and native device verification still need account access and a running deployment. The existing in-process limiter is not a distributed production rate limit; complete [the production gates](PRODUCTION.md) before a public production rollout, including ingress limits and catalog review.

For PostgreSQL, use your provider's backup/export facilities or an encrypted `pg_dump` made from your computer. Do not use the SQLite-only backup command on a PostgreSQL database. Keep dumps private, test restores into an isolated database, and reconcile withdrawn consent/deleted participants before reopening a restored system. Free hosting is not a promise of unlimited retention or disaster recovery. See [backup policy](BACKUP.md).

## Alternative free API host

[Render Free web services](https://render.com/docs/free) can run the existing Docker API, but sleep after 15 minutes without traffic and have other free limits. Render's free PostgreSQL expires after 30 days, so use a separate durable database provider for this setup. The same local training-worker arrangement is still required; a sleeping free web service is not an always-running training worker. No alternative is provisioned automatically or billed.
