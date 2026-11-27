# Train Fitness-AI with your own data

For the **already-trained exercise/muscle category model**, see [EXERCISE_KNOWLEDGE.md](EXERCISE_KNOWLEDGE.md). This guide covers the separate participant-outcome RPE network.

This build includes an actual CPU neural network. It has two hidden layers (32 and 16 tanh units), backpropagation, Adam optimization, validation-based early stopping, saved weights and an inference path in the workout service. It uses NumPy 2.2.6 so it can train without a GPU, ChatGPT, an LLM provider or an external API key. It predicts set difficulty (RPE); it is not a language model and cannot diagnose injury or establish which program causes better results.

No model trained on real users is included. Synthetic test models are created only in temporary test databases. The app starts with deterministic programming rules.

## First setup

Install the backend dependencies from the project README, activate its virtual environment, and open a terminal in `backend`:

```bash
python -m fitness.setup
uvicorn fitness.api:app --host 0.0.0.0 --port 8000
```

Keep that server running. Open the mobile app as described in the README. In **Settings → Help improve training**, enable **Contribute my workout data**. This choice is separate from account creation and nutrition. Other users can independently opt in. They never see one another's records.

The exercise tutorial library is available immediately. Automatic workouts still require professionally reviewed exercise metadata; see CATALOG_REVIEW.md. Media ownership does not automatically approve programming metadata. You can use the historical CSV import while that review is underway.

## Feed data through workouts

Create a plan after opting in, log actual sets, synchronize the pending logs, and finish the workout. Collection occurs transactionally on completion. The first prediction task accepts only sets with known prescribed load, matching completed reps/load, no reported pain and no skip. Body-weight prescriptions can use 0 kg. A changed load is legitimate operational history but is excluded from this initial matched-prescription task. Only pre-prescription experience/readiness/history features are snapshotted; actual RPE is the outcome label.

Consent enabled after a plan was created does not backfill that plan. Re-enabling consent after withdrawal does not revive old contributions. Settings shows eligible sets, imports awaiting review, and whether the deployed model is in rules, shadow, or live mode. Reading a status does not train a model.

## Easier data entry for participants

Use the **Contribute** tab to enter your own workout or an earlier one without CSV. Missing answers are allowed, and the receipt explains training eligibility. Guided records enter the operator review queue before neural training. See COLLECTING_DATA.md.

## Feed historical records through CSV

A header-only template is included at `data/training-template.csv`. You can also generate a fresh one:

```bash
python -m fitness.ml template --output my-training-data.csv
```

Fill one row per set. Do not invent missing historical readiness or prescription information. Use `false` for pain and skipped; pain/skipped outcomes stay in normal workout logs, not this RPE training task. Use kilograms and Unix UTC seconds. Exercise IDs must exist in the imported catalog. Event IDs must be stable 16–80 character letters/digits/underscore/hyphen strings; session IDs are 8–80 characters. All sets from one real workout must share a session ID, and every row must belong to the account whose ID you specify.

| Column group | Meaning |
| --- | --- |
| event_id, session_id, exercise_id, occurred_at | Source identity, real workout grouping, catalog exercise ID and outcome time |
| experience | 0–6 experience scale from the profile |
| sleep_hours, energy, soreness, stress | Values known before the prescription; energy 1–5, soreness/stress 0–5 |
| reps, load_kg, target_rpe, set_number | Planned values before the set |
| previous_load_kg, previous_rpe, history_sessions | Previous completed-session context, known before the plan; use history_sessions=0 when no history exists, previous_load_kg=0 and previous_rpe=target_rpe in that case |
| pattern | One of the enum values in fitness/learning_contracts.py, e.g. squat or horizontal_push |
| actual_rpe, actual_reps, actual_load_kg | Measured/self-reported outcomes; reps/load must match the plan for this task |
| pain, skipped | Both must be false for eligibility |

Your account ID appears under **How training works** in Settings. On your own backend computer:

```bash
python -m fitness.ml import-csv my-training-data.csv --user-id YOUR_ACCOUNT_ID
```

Imports are atomic and idempotent: repeating identical event IDs adds no duplicates; changing their payload causes a conflict. Maximum file size is 10 MB. API clients may alternatively POST up to 500 records to `/api/v1/learning/examples`, using their own train-scoped key. They cannot submit another user's ID or self-approve their data.

Inspect source records and grouping before approving an import. The operator can review pending imports for the account:

```bash
python -m fitness.ml review-imports --user-id YOUR_ACCOUNT_ID --reviewer "Your name" --evidence "Reference to the checked source records"
```

This records data-quality review, not a claim of medical validation. Synthetic or fabricated outcomes must never be approved into a live training database.

## Train the network

In a second terminal, with the backend virtual environment activated:

```bash
python -m fitness.ml train
python -m fitness.ml status
```

The command collects currently eligible records, trains the network, evaluates it and saves numeric weights plus evaluation/provenance in the database. It does not replace the running model automatically. Repeating it with unchanged eligible data returns the existing candidate rather than retesting the same dataset.

- With too little data: `waiting_for_data`; add more suitable records.
- Small personal pilot: at least 30 eligible rows with enough distinct sessions for train/validation/test partitions (normally at least five sessions). A real neural candidate can train, but remains experimental.
- Shared candidate: user-disjoint train/validation/test partitions; latest sessions of training users are held out separately for longitudinal evaluation.
- Default shared deployment gates: at least 500 eligible rows and 20 contributors, plus at least 30 future-session examples from five training users. These are conservative engineering thresholds, not universal data requirements or evidence of clinical effectiveness.
- Validation, new-user test and future-session mean absolute RPE error must be at most 1; 90th percentile absolute error at most 2. The model must improve both the target-RPE baseline and training-mean baseline by at least 5%. Available beginner/experienced subgroups must not materially regress.
- If a model is already deployed, require at least 30 new test records and improved error against it. Do not tune repeatedly against the same held-out test set.

Records are deduplicated by contributor/session/exercise/set and capped at 1,000 per contributor. Evaluation MAE averages per-user errors so one prolific contributor does not dominate. Training batches are still row-weighted within that cap. Suspicious-input detection, broader subgroup audits and defenses against coordinated data poisoning need further work before public deployment.

## Evaluate and release a candidate

```bash
python -m fitness.ml show MODEL_ID
python -m fitness.ml activate MODEL_ID --mode shadow --reviewer "Reviewer name" --evidence "Evaluation report reference"
```

Only a candidate with passing gates can activate. Shadow mode records predictions in saved recommendation reasoning while leaving prescriptions unchanged. The report contains dataset hash, sample lineage and split membership for operator audits. It must remain private.

After reviewing real-world shadow results and the programming policy, an operator may enable bounded live assistance:

```bash
python -m fitness.ml activate MODEL_ID --mode live --reviewer "Reviewer name" --evidence "Shadow evaluation and policy review reference"
```

Live assistance only reduces an already prescribed positive load by 5% when predicted effort exceeds target by more than 1 RPE and at least three historical sessions exist. It never increases load, changes exercise eligibility, ignores pain, or approves unreviewed metadata. Inputs outside the training feature ranges, unknown exercises, missing context, altered weights and unsupported feature versions fall back to rules. This range check is a conservative applicability filter, not calibrated individual uncertainty.

To stop neural assistance or roll back:

```bash
python -m fitness.ml disable
python -m fitness.ml activate PREVIOUS_PASSED_MODEL_ID --mode shadow --reviewer "Reviewer name" --evidence "Rollback reason"
```

A withdrawn or quarantined model cannot be revived by this command.

## Collect and train automatically

```bash
python -m fitness.ml watch --interval-hours 24
```

Leave this process running on your backend host, or supervise it as a service. It trains/evaluates a candidate every 24 hours when eligible data changes. It never automatically activates a candidate. Docker Compose includes an optional `learning` profile for the same worker. Stopping your computer stops local collection/synchronization and training; a continuously available hosted backend is a separate deployment task.

## Data withdrawal and backups

Withdrawal deletes the account's learning examples and erases/invalidates all current database models influenced by that account, including evaluation participation. Operational workout history is retained until account deletion. Training captures consent tokens and rechecks them before saving or activating a model, so withdrawal during training cannot resurrect contributions.

Read BACKUP.md for consistent database/model snapshots, retention and restore quarantine. Existing off-host backups and exported CSV files are not automatically erased by the app; the operator must apply retention/deletion policies. Data is pseudonymous, not anonymous. No production dataset, credentials, API keys or trained user weights belong in a Git repository or the source ZIP.

### Initial model scope

The first model uses movement-pattern indicators and numerical context; it does not yet learn exercise-specific embeddings or user embeddings. It serves only catalog exercise IDs seen in training, but cannot distinguish two exercises with identical feature vectors. This limitation must be assessed during shadow review. For in-app examples, `occurred_at` uses the saved session's creation time for stable session ordering when offline logs arrive late; it is not claimed to be a measured set-completion timestamp.
