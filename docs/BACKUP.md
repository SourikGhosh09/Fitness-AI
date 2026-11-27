# Backup and restore

Neural weights, feature normalization, dataset hashes, evaluations, review records and deployment pointers are stored transactionally in the same database as workout history. Backing up the database captures this state consistently. The original exercise data/media and source code are reproducible from the source package and should be versioned separately.

## SQLite development installations

From backend with the virtual environment activated:

```bash
python -m fitness.backup create ../backups/fitness-2026-09-11.zip
python -m fitness.backup restore ../backups/fitness-2026-09-11.zip --output ../backups/restored-review.db
```

Use a new filename for each backup. Existing destinations are never overwritten. Backup uses SQLite's online backup API, checks database integrity and includes a SHA-256 manifest. Restore rejects unexpected archive members, excessive sizes and checksum mismatches. Newly created files use owner-only permissions where the operating system supports them.

These ZIP files are **not encrypted**. Store them on an encrypted disk or encrypted object storage with restricted access. They contain account password hashes, personal records, health-related feedback and model data. Do not upload them to GitHub or distribute them with the app.

Restoration is deliberately quarantined: all API/session tokens are revoked, shared-learning consent is disabled, training examples and guided contributions are removed and model versions are marked quarantined. Archived weights remain inspectable but cannot activate. Obtain fresh consent and retrain. Reconcile account deletions since the snapshot before connecting any restored database to a public API. Do not use an old backup to undo a user's deletion request.

## PostgreSQL deployments

The SQLite helper refuses PostgreSQL URLs. Use your database provider's encrypted backups and point-in-time recovery (PITR), or PostgreSQL `pg_dump`/`pg_restore`. With libpq environment variables configured securely on the server (PGHOST, PGPORT, PGDATABASE, PGUSER and a protected credential mechanism):

```bash
pg_dump --format=custom --file=fitness-backup.dump
pg_restore --dbname=fitness_restore_review --no-owner --no-acl fitness-backup.dump
```

Restore into an isolated database, never the live one. Apply the same quarantine before exposing it:

```sql
BEGIN;
UPDATE api_keys SET revoked = true;
UPDATE learning_deployment SET model_id = NULL, mode = 'shadow';
UPDATE learning_consent SET enabled = false;
UPDATE notion_links SET enabled = false;
DELETE FROM notion_imports;
DELETE FROM notion_pages;
DELETE FROM notion_purges;
DELETE FROM notion_worker_state;
DELETE FROM learning_examples;
DELETE FROM user_contributions;
UPDATE learning_models SET status = 'quarantined';
COMMIT;
```

Reconcile the current deletion/consent ledger, run migrations and integrity checks, then test sign-in, exercise media mapping and workout history using test accounts. Provider-specific PostgreSQL backup automation/PITR is a deployment task, not enabled by the source package. The local restore test covers SQLite; PostgreSQL commands require validation on your chosen host.

## Proposed operating policy

For a pilot, schedule a daily encrypted off-host copy and retain a short documented window (for example, seven daily backups). Before public release, select a recovery-point/recovery-time objective, configure managed PITR if required, restrict backup roles, monitor failures and perform regular isolated restore drills. Keep an independent deletion ledger so recovery cannot resurrect deleted accounts. These schedules are recommendations, not currently configured services.

Reference: Python's [SQLite online backup API](https://docs.python.org/3/library/sqlite3.html#sqlite3.Connection.backup). Backup hashes detect accidental alteration; they are not signatures proving archive authenticity. Restore only backups from your trusted storage.

After a restore, keep the Notion worker stopped until current withdrawals/deletions have been reconciled. Rebuild required cleanup jobs from the current deletion ledger, not the stale backup. Fresh Notion opt-in issues a new code.
