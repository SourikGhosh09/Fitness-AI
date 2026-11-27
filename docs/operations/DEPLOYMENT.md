# Deployment

Current architecture supports FastAPI + PostgreSQL for hosted backend and Expo mobile clients; SQLite remains local development. Existing provider-specific preparation guides are `VERCEL_DEPLOYMENT.md`, `RENDER_NOTION_DEPLOYMENT.md` and `GITHUB_DEPLOYMENT.md`; none alone proves a live production deployment.

Before deployment: provision PostgreSQL and required server secrets, use HTTPS, run Alembic migrations, restore/verify catalog/media assets, configure background sync/training workers only where required, run backend/mobile checks, verify auth/media/account flows, configure backups/monitoring, and perform a rollback rehearsal. Never run model training or migrations opportunistically inside serverless request handlers.

Rollback: stop new deployment/workers, restore prior application artifact, apply only documented reversible migration procedure, validate DB integrity/auth/core workout reads, and quarantine learning deployment if model provenance is uncertain.
