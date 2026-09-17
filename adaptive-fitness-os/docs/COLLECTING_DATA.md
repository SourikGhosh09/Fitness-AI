# Collect workout data from other users

The app now includes a **Contribute** tab with a guided three-step form. Each person creates their own account on the same Fitness-AI backend. They do not need to type account IDs, exercise IDs, JSON or CSV rows. The form records their own activity; it does not prescribe or approve a workout.

## What participants do

1. Open Contribute and choose whether to participate. Sharing is voluntary and is separate from normal app use. The consent text explains the data used, private account separation, and withdrawal.
2. Answer a quick before-workout check-in: date, experience, sleep, energy, soreness and stress. For an earlier workout, answer only what is remembered. All context questions can be left unknown.
3. Search the exercise library by name, select the actual exercise and log the sets. Reps and kilograms have plus/minus controls. Effort and pain use labeled tap choices. Add set copies reps and weight; effort and pain reset to unknown so feedback is never silently copied.
4. If the original prescription is known, optionally enter the planned reps, weight and effort. Never enter actual results as if they had been the original plan. The current form supports one common target across that exercise's sets; leave it unknown if targets varied. The structured API/CSV route remains available for variable per-set prescriptions.
5. Review and send. Optional enjoyment and exercise duration can be included. The receipt explains which sets are complete enough for training review and which have missing information or other exclusions.
6. Add another exercise from the same workout without re-entering the check-in, or start a different workout log. Recent submissions are visible only to their owner.

No extra training, unsafe exercise or health hardware is required. No reward is issued for submitting more records. Participants should record their normal routine and can skip any optional question. Reported pain is saved as feedback and excluded from this RPE training task.

## Drafts and connectivity

Form drafts are saved in device SQLite after edits. The cache is account/session scoped, and draft writes are serialized with sign-out erasure. After a successful initial connection, an existing draft can be edited with poor connectivity. Exercise results previously cached by the same search can be reused offline; first-time exercise searches need a connection.

Sending requires a connection. The exact submission and its stable event ID are saved before the request. If the response is lost, Send saved submission retries that same payload. The server returns the existing receipt instead of counting the submission twice. A session/exercise uniqueness constraint also prevents a second event ID from duplicating the same exercise in the same logged workout.

A draft is not claimed to be synchronized until the server acknowledges it. Consent is checked at submission and review. Sign-out erases device drafts and pending logs. Expired or changed credentials need sign-in again; another account cannot send an old account's draft through the contribution API wrapper.

## What enters neural training

Partial contributions are useful collection records but are not automatically valid neural-network examples. The first model requires:

- Known before-workout context and original prescription.
- Known actual RPE, matching completed reps/load, no skip and an explicit no-pain report.
- A reviewed movement-pattern classification.
- Either an explicit first-time exercise declaration or suitable earlier reviewed contributions supplying historical context.

An unknown answer stays null. Actual and planned values remain separate. Skipped ordinary workout sets now support null RPE too, so their history does not invent an effort rating. Earlier-history features are frozen when a contribution arrives, using only earlier reviewed sessions; reviewing future records cannot leak their outcomes into that snapshot.

The form accepts ordinary exercise records before the catalog's programming metadata is approved. This permits collection during the review process, but the metadata must be approved before affected records can become training examples. The owner can re-review such a record after metadata approval; the participant does not need to resubmit it. Truly missing historical observations cannot be recovered by guessing.

## Owner review workflow

From backend with the virtual environment activated:

```bash
python -m fitness.collect report
python -m fitness.collect show CONTRIBUTION_ID
python -m fitness.collect review CONTRIBUTION_ID --reviewer "Your name" --evidence "Reference to the checked source record"
python -m fitness.ml train
```

The private report shows contributor/submission counts, the pending queue and frequent completeness gaps. Show lets the operator inspect a record; Review validates its current eligibility and copies eligible examples into the existing neural training dataset, with reviewer provenance. Repeating review does not duplicate examples. Reviews do not certify clinical effectiveness or data truthfulness beyond the operator's actual checks.

Ordinary user API keys cannot inspect other users, operate this review queue or activate a shared model. Training and deployment retain the evaluation gates described in TRAINING.md. A recurring training worker can discover newly reviewed data without any ChatGPT involvement.

For an operator-only snapshot of consenting participants' guided data:

```bash
python -m fitness.collect export --output ../training-private/contributions.jsonl
```

Create the private destination folder first. The command refuses to overwrite an existing file and uses owner-only permissions where supported. The export omits account email/name but contains pseudonymous identifiers and health-related observations. Encrypt it, restrict access, and reconcile later consent withdrawals before reuse. It is not an anonymous public dataset.

## Withdrawal and backup

Turning off shared learning deletes that person's guided contributions and model examples from the live database, and invalidates/erases models influenced by them. Account deletion follows the same path. Models, contributions and feedback are covered by database backup. SQLite restore removes restored guided contributions as part of quarantine. Hosted PostgreSQL restoration must do the same; see BACKUP.md. Offline exports and old backups require separate operator retention/deletion handling.

## Getting participants connected

This source package does not create a public invitation URL, hosted server or APK. Local tests use Expo Go with the configured backend, as described in README.md. For participants outside your local test network, deploy a reachable HTTPS backend and distribute an Android/iOS test build configured to use it. Each participant then registers their own account. Do not share a single account or API key among participants.

Remaining work before public rollout: native device usability/accessibility testing, hosted HTTPS operation, account verification/recovery, production abuse controls, broader data-quality/poisoning checks and a privacy/retention policy for your actual deployment. The current owner review queue is a CLI, not a graphical administration portal.
