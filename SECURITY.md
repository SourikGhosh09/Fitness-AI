# Security policy

Development-stage software. Do not use real health data in an internet-facing deployment until production gates close.

Report vulnerabilities privately to the repository owner's chosen security contact; no contact address is prefilled. Never publish an exploit containing user records or live credentials. Scope and owner checks belong in application services, not only the UI. Personal API keys cannot bypass them.

Credential hygiene: passwords are Argon2-hashed; API/session tokens are random and hashed at rest. Credentials must not be committed, included in app bundles or passed to an LLM. Configure infrastructure/provider secrets through the deployment secret manager.

The app has no independent medical authority, and an LLM adapter must not weaken deterministic safety policy. A health restriction cannot be cleared by a model-generated assertion.
