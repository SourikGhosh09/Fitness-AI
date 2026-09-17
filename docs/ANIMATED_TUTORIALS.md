# In-app exercise animations

The supplied `exercises-dataset-main.zip` contains 1,324 animated GIF tutorials and 1,324 matching thumbnails. The uploaded exercise JSON exactly matches the pinned dataset already used by this project. All 2,648 media files are included under `data/tutorial-media`, with hashes, dimensions and frame counts in `data/tutorial-media-manifest.json`.

The project owner explicitly confirmed having the media rights and supplied this archive for in-app playback. That authorization is recorded in `data/media-authorization.json`. It is a record of the owner's statement, not an assertion of independently verified legal ownership. No expiry was stated, so this authorization has no invented expiration date. Existing Gym visual attribution remains visible.

## Start and play

From `backend`, with the Python dependencies installed:

```bash
python -m fitness.setup
uvicorn fitness.api:app --host 0.0.0.0 --port 8000
```

Setup runs migrations, verifies the supplied assets and exact dataset, imports exercises and records the owner's media authorization. Repeating setup does not duplicate grants or reverse an operator's revocation. Exercise metadata approval remains separate from permission to play a tutorial.

In the mobile app, sign in, open **Library**, search an exercise and tap **Watch tutorial**. The same control appears on each exercise in a generated workout. The GIF plays inside the app; Stop removes it, and Play restarts it. Backgrounding the app stops playback. The original GitHub page remains an optional source link, not a requirement for playback.

## Delivery and credentials

1. The authenticated descriptor endpoint returns a relative application media path, never a third-party animation URL.
2. The mobile player attaches the sign-in credential only to validated media paths on its configured API origin.
3. The backend checks the credential, read scope, current media authorization, exact asset path and file integrity before returning GIF/image bytes.
4. Media responses use their actual image content type and `Cache-Control: no-store`. The native image player disables disk and memory caching.

Endpoints:

- `GET /api/v1/exercises/{exercise_id}/tutorial`
- `GET /api/v1/exercises/{exercise_id}/media/gif`
- `GET /api/v1/exercises/{exercise_id}/media/image`

The default media directory is the repository's `data` directory. Docker copies it to `/data` and sets `FITNESS_DATA_DIR=/data`. Set that variable to another absolute data directory if needed. In Compose, the setup job verifies/imports the media before the API starts.

Playback requires a connection to the running backend. Offline set logging and written instructions continue to work; offline animation downloads are not implemented. There is no GitHub hosting dependency for GIF playback.

## Authorization maintenance

Grants are operator-managed records tied to specific media paths and source commits. Ordinary user API keys cannot create media grants. Operators can revoke grant IDs with `python -m fitness.tutorials revoke GRANT_ID`. New bytes, mappings or source commits must be reconciled with the imported asset manifest and authorization scope. Setup checks every file hash rather than silently accepting replaced assets.

The owner's supplied files and authorization support this project. They do not relicense the media to unrelated recipients or replace the original source notices. See LICENSING.md.

## Validation limits

All source assets were checked, actual authenticated GIF responses were tested, and Android/iOS bundles were generated. Native GIF display has not been tested on a physical phone or simulator in this environment. No APK or IPA is produced by JavaScript bundle export.
