# Production readiness and operations

This package is for development until these release gates are met.

1. Qualified exercise/clinical reviewers approve metadata, screening, training policy, preparation/cooldown guidance and population scope. Do not bulk-approve heuristic records or test fixtures. Maintain reviewer identity, evidence and policy versions.
2. Implement missing programming/assessment requirements and validate multi-goal scheduling. Add performance-at-comparable-load analysis, weekly volume caps, recovery trend handling, exercise-specific progression and conflict tradeoffs.
3. Owner-supplied media has been integrated using their explicit authorization. Preserve the supplied ownership/attribution records and confirm any broader release or redistribution scope with the owner.
4. Deploy PostgreSQL with encrypted transport/storage and least-privilege credentials. Run migration as a separate job. Configure TLS ingress, 64 KB JSON body limit, distributed authentication/IP/user limits, bounded timeouts, trusted proxy allowlist and restricted CORS. The in-process limiter is a development defense, not a distributed production control.
5. Complete verification/reset, session renewal, session inventory/revocation, consent/versioning, structured audit coverage, secure backups/deletion retention policy and operational incident procedures. Never log credentials, raw health data or free-form coach inputs by default.
6. Enable database encryption for sensitive device caches, test offline account isolation, add conflict-resolution/replan UI and validate stale plans after pain/restriction changes. Review device backup exclusions and secure-store behavior.
7. Execute real PostgreSQL concurrency tests and race tests for duplicate set/XP submissions; data restore rehearsal; privacy export/deletion coverage; load and penetration tests; dependency/security scans. Current local tests use SQLite.
8. Execute native Android/iOS builds, accessibility and permission-denial tests, offline crash/restart tests, and camera/wearable evals before enabling those integrations. Configure signing using protected CI secrets outside Git.
9. Deploy staging, record version and migration IDs, use synthetic smoke-test accounts, verify rollback, then stage the production rollout. Disable recommendation generation on unexpected safety errors. Do not train through an unavailable safety service.

## Deployment commands

Copy `.env.example` to `.env`; set strong credentials. For Compose the database hostname in DATABASE_URL must be `database`, not localhost. From the repository root:

```bash
docker compose up --build -d
# The setup service imports and verifies the supplied dataset and animations automatically.
```

API binds to loopback by default. Put an authenticated TLS ingress in front before remote use. Catalog review is a separate operator task. No cloud infrastructure has been provisioned by this package.

## Operations design

Health endpoint verifies database availability. Add structured request IDs, error counts, latency histograms, auth-failure rates, sync-conflict counts and safety-block metrics without sensitive payloads. Back up daily with encrypted storage and tested point-in-time recovery. Target availability/latency/RPO/RTO must be established and load-tested; none is claimed yet.

Rollback code to prior image only when schema-compatible; forward-fix migrations by default. Do not casually downgrade production migrations with user data. Revoke leaked app keys immediately, rotate infrastructure/provider secrets, audit affected accesses and investigate exposure before resuming traffic.
