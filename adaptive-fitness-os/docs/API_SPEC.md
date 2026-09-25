# API Specification

The generated contract in `openapi.json` is the endpoint-level source of truth. API prefix is `/api/v1`. Authentication uses opaque bearer sessions or scoped API keys where permitted; authorization derives the owner from credentials.

Major groups: authentication/profile/readiness, workout generation/retrieval/completion/substitution, set logging, exercise/library/media/knowledge, coach, contributions, learning consent/status/import, nutrition, integrations, API keys and account export/deletion. Validation errors use typed FastAPI responses; conflicts such as duplicate/inconsistent immutable events use explicit 409 responses.

Any endpoint change must update implementation tests and regenerate/check `openapi.json`. Future weekly-plan endpoints must expose schedule state and explanation without allowing clients to bypass safety or forge historical completion.
