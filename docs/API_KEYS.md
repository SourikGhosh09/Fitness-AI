# Fitness OS API keys

## Credential types

| Credential | Issuer | Use |
| --- | --- | --- |
| Sign-in session | This backend | App access; credential management; one-day expiry |
| Personal API key | This backend | External clients calling this user's Fitness OS API |
| External LLM provider key | Chosen provider | Optional inference; not issued by Fitness OS |

Register through `POST /api/v1/auth/register` with email and a password of at least 12 characters. The response contains a sign-in token in `key`. Sign-in through `/api/v1/auth/login` returns the same response shape. Authentication uses `Authorization: Bearer <secret>`.

Create a key through `POST /api/v1/api-keys`, authenticated with the sign-in session:

```json
{"name":"My integration","scopes":["read","train","coach"],"expires_days":30}
```

Only request scopes you need. `read` accesses profile/library/history; `train` updates profiles, readiness, nutrition and workout records; `coach` accesses the coach endpoint. The response contains `id`, one-time `key`, `expires_at`, and `scopes`.

List key metadata with `GET /api/v1/api-keys`. Revoke with `DELETE /api/v1/api-keys/{id}`. Keys cannot list or create other keys or export/delete accounts. Expired/revoked credentials return 401; insufficient scope returns 403.

Secrets contain 256 bits of cryptographic randomness. Only a digest is persisted. Store mobile sign-in sessions in SecureStore. Never put provider secrets, sign-in tokens or personal API keys in Git, analytics, screenshots, prompts, or EXPO_PUBLIC variables. A lost personal key cannot be recovered; create a new one and revoke the old one.

No live service or user credential was deployed/generated for this package. Therefore there is no externally usable key to hand over yet. Issuance becomes available when the backend runs.
