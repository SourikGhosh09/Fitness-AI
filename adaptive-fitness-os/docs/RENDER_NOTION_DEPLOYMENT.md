# Render API and scheduled Notion collection

The mobile app connects to the Render API over HTTPS. Neon stores persistent
accounts, observations and model artifacts. Render's free filesystem is disposable.
Tutorials are restored from the pinned upstream commit and checked against the
owner-authorized manifest during builds. No participant data belongs in GitHub.

Build command: `bash scripts/render_build.sh`

Start command: `PYTHONPATH=backend uvicorn fitness.api:app --host 0.0.0.0 --port $PORT`

Set Render's secret `DATABASE_URL` to the dedicated `fitness_ai` Neon database.
The build applies Alembic migrations and imports the verified catalog. Existing
exercise safety metadata stays unapproved until separately reviewed.

## Enable hourly Notion synchronization

1. Create an internal integration at https://www.notion.so/profile/integrations.
   Give it read and update content access, then share only the Fitness AI collection
   with it. Update access supports clearing/trashing withdrawn imported records.
2. In GitHub repository Settings → Secrets and variables → Actions, add secrets
   `NOTION_TOKEN` and `FITNESS_DATABASE_URL_DIRECT`. Use Neon's **direct**, TLS-enabled
   connection string for database `fitness_ai`, not the pooler, because the importer
   uses session advisory locks. Never paste these secrets into source code or chat.
3. Add repository variable `NOTION_SYNC_ENABLED` with value `true`.
4. Open Actions → Notion synchronization → Run workflow. Check the run succeeds.
5. In the native app, create your account, complete the profile, opt into shared
   learning and enable Notion collection. Copy the app-issued participant code to
   your Notion observations. Demo rows and rows without current consent are excluded.

The scheduled job imports edits about hourly (GitHub scheduling can be delayed).
It attempts candidate training only from reviewed eligible examples. A new row
does not automatically approve itself or activate new weights. Insufficient data
returns a waiting status. Shared release needs at least 500 eligible sets from 20
users plus evaluation and operator review. Disable the repository variable to pause.

Standard GitHub-hosted runners are free for public repositories:
https://docs.github.com/en/actions/concepts/billing-and-usage
No observations or trained participant models are uploaded as public artifacts.
Only aggregate status is logged. Keep dependencies and workflows reviewed because
workflow code can access secrets. GitHub may disable inactive public schedules;
monitor Actions and the app's last successful sync time.

Render free services sleep after inactivity and share the workspace's free hours:
https://render.com/docs/free. Cold starts are expected. This setup is an experimental
pilot, not a completed production release or a guaranteed always-on service.

## Native app testing

Set `EXPO_PUBLIC_API_URL` in `apps/mobile/.env` to the deployed HTTPS API origin
(see `apps/mobile/.env.example` for the exact variable used by this source).
Run `npm ci` and `npx expo start` from `apps/mobile`. Use an Android/iOS development
client compatible with the checked-in Expo SDK. See the root README and EAS config
for installable builds. Deployment of this API does not create an APK.
