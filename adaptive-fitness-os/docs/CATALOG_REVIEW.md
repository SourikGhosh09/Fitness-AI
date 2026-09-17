# Catalog review workflow

The importer preserves source text and translations without treating them as individualized recommendations. Initial enrichment suggests a movement pattern only from exercise names, with provenance/confidence. Safety tags, skill, fatigue, suitability and other uncertain fields are unverified. All 1,324 imported records therefore start in `needs_review`.

Reviewers work on separate JSON records; never edit `data/exercises.json`. Each review record has `exercise_id`, `review_note` and `metadata`. The metadata requires an assessed pattern, numeric skill 0–6, fatigue 0–1, suitability values 0–1, progression strategy and `safety_reviewed: true`. These are application taxonomy ratings, not validated clinical scores.

A qualified reviewer must determine those values before applying them. This repository intentionally supplies no pretend approvals. The executable schema/format is in `fitness/review.py`.

```bash
cd backend
python -m fitness.review /absolute/path/reviewed-exercises.json --reviewer reviewer-identifier
```

On source refresh, unchanged records preserve review; changed source hashes invalidate approval without erasing the enrichment history's latest values. The pinned importer rejects unexpected source bytes. To upgrade, inspect upstream changes, update the commit/blob constants and licensing report, rerun validation, then review changed exercise metadata.

Media references are local upstream paths such as `images/{id}-{media_id}.jpg` and `videos/{id}-{media_id}.gif`; keep the explicit source paths instead of reconstructing from numeric IDs. Media playback is now enabled from the uploaded files using the owner’s authorization. This does not approve clinical or training metadata.
