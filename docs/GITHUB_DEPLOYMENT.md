# Deploy without ChatGPT's Vercel connection

The `Deploy Fitness AI` GitHub Actions workflow runs in your GitHub account. Its
Vercel token is stored privately in GitHub Actions secrets. ChatGPT does not need
the token. This is a separate authorization route; it does not change the failing
ChatGPT connector's permissions. The token must itself be authorized for sourik2.

## One-time authorization

1. Sign in to the Vercel account that owns `sourik2/fitness-ai` and open
   https://vercel.com/account/tokens. Create a token named `Fitness AI deployment`,
   scoped to the `sourik2` team if that scope is offered. Set a short expiry that
   covers deployment; revoke it afterward or rotate it when required.
2. Open https://github.com/SourikGhosh09/Fitness-AI/settings/secrets/actions.
   Add a repository secret named `VERCEL_TOKEN` and paste the token there.
   Do not paste it into a chat, issue, source file, or screenshot.
3. Add `VERCEL_ORG_ID`: copy the **Team ID** from the sourik2 team's Settings →
   General page. It starts with `team_`; the name `sourik2` is not the ID.
4. Add `VERCEL_PROJECT_ID`: copy **Project ID** from fitness-ai → Settings →
   General. It starts with `prj_`; the name `fitness-ai` is not the ID.

IDs are identifiers, not passwords; they are kept as secrets here to match the
standard Vercel CI configuration. The helper uses an ephemeral private auth file
outside the checkout, so the token is not embedded in CLI arguments or uploaded
with the application. Fork pull requests cannot trigger this deployment workflow.

## Database prerequisite

Before deploying, connect the new fitness database to this Vercel project and
configure `DATABASE_URL` for the environment selected in Actions. Use the pooled
PostgreSQL URL with `sslmode=require` or stronger. Keep the travel database separate.
Use a separate database for previews. The complete initialization and Google Forms
instructions are in [VERCEL_DEPLOYMENT.md](VERCEL_DEPLOYMENT.md).

Database migrations/import are deliberately not run by this workflow. The database
must be initialized using `python -m fitness.setup` against its direct PostgreSQL
URL before the API is ready. A successful deployment by itself does not prove the
database has been initialized. The API rejects missing/SQLite/non-TLS database
configuration on Vercel. Training remains a separate worker on your computer.

## Run

The source and workflow must be present on the repository's `main` branch.
Open Actions → Deploy Fitness AI → Run workflow. Select `main` and choose preview
first, then production once the environment has been tested. The workflow runs
backend tests, pulls the configured Vercel environment, builds once and uploads
the prebuilt application. The resulting URL appears in the run summary.

Keep preview protection enabled. Test the deployment via your signed-in Vercel
session; verify `/healthz`, `/docs`, sign-in and tutorial access. Production users
need a reachable production origin. Configure the mobile API origin and Google
Forms bridge only after these runtime checks succeed.

The workflow is manual-only; it does not deploy on every push. Existing Vercel Git
integration may still trigger its own builds on pushes. No paid integration, Pro
upgrade, scheduled GPU job or billing changes are included. The workflow's cloud
execution is unverified until authorized credentials are added and a run succeeds.

References: [Vercel's GitHub Actions guide](https://vercel.com/kb/guide/how-can-i-use-github-actions-with-vercel),
[GitHub Actions secrets](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets).
