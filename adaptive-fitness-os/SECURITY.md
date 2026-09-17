# Security policy

Development-stage software. Do not use real health data in an internet-facing deployment until production gates close.

Report vulnerabilities privately to the repository owner's chosen security contact; no contact address is prefilled. Never publish an exploit containing user records or live credentials. Scope and owner checks belong in application services, not only the UI. Personal API keys cannot bypass them.

Credential hygiene: passwords are Argon2-hashed; API/session tokens are random and hashed at rest. Credentials must not be committed, included in app bundles or passed to an LLM. Configure infrastructure/provider secrets through the deployment secret manager.

The app has no independent medical authority, and an LLM adapter must not weaken deterministic safety policy. A health restriction cannot be cleared by a model-generated assertion.

## Neural training boundary

Global training/review/activation is operator-only through the backend CLI. User tokens can contribute only their own records after explicit consent, and imports remain pending until reviewed. Real data, model-bearing database backups and training CSVs must remain outside source control. Numeric JSON artifacts avoid executable model loading; feature version, shape, finiteness, digest and domain checks guard inference. Models never approve exercise safety. Shared-learning withdrawal deletes examples and erases influenced model artifacts in the active database. Backups require separate encrypted retention/deletion handling; restore quarantines learning and revokes all access tokens.

This implementation is not a complete defense against coordinated poisoning, inference-based privacy attacks or operator compromise. Public deployment requires access reviews, monitored data-quality review, broader subgroup evaluation, encrypted backups and a tested deletion reconciliation process.
