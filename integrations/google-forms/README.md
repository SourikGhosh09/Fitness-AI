# Fitness AI — Google Form connection

The integration code is ready. **A live Google Form has not been created in your account, and the backend has not been deployed.** This session exposes no Google Forms/Apps Script write action. The installer below creates the native form and response spreadsheet after you authorize it in your Google account.

After activation: participant submits or edits a response → authenticated backend synchronization → data validation → candidate network training → evaluation → optional automatic shadow deployment. ChatGPT is not part of this running pipeline.

## One-time activation

You need the updated backend from `adaptive-fitness-os.zip`, a public HTTPS address for it, and your Google account. A phone's localhost/LAN address cannot receive Google's requests. The script and backend share a secret; do not post that secret in this chat or put it in the form.

1. Open [Google Apps Script](https://script.google.com/) and create a new project named **Fitness AI Survey**. Replace its `Code.gs` with the supplied `Code.gs`.
2. In Project Settings, enable viewing the manifest and replace `appsscript.json` with the supplied file. The script uses Google Forms, Sheets, triggers and outbound HTTPS permissions. It does not ask for Gmail or send invitations/messages.
3. Run **createSurvey** and authorize the requested Google permissions. This creates an initially unpublished form, a private response spreadsheet, and organizer sheets. Read the execution log for the actual form ID and edit/spreadsheet links. No data is submitted by running this installer.
4. Configure the backend's environment:

   ```text
   SURVEY_FORM_ID=<the actual form ID from step 3>
   SURVEY_WEBHOOK_SECRET=<a random secret of at least 32 characters>
   ```

   Generate a secret locally, for example `python -c "import secrets; print(secrets.token_urlsafe(48))"`. Save it in your server secret settings.
5. In the Apps Script project's **Script Properties**, set:

   | Property | Value |
   |---|---|
   | API_BASE_URL | Your public HTTPS origin, such as your actual backend domain; no `/api/v1` suffix |
   | WEBHOOK_SECRET | The same secret as the backend |
   | TIME_ZONE | `Asia/Kolkata` by default; change before collection if needed |
   | EXERCISE_IDS | Optional comma-separated catalog exercise IDs, up to 100; omit for the starter selection |

   `FORM_ID` and `SHEET_ID` were set automatically. Do not replace them with example values.
6. Install dependencies and run `python -m fitness.setup` from `backend` to migrate through **0006** and import the dataset. Restart the API with the survey environment variables. Start one dedicated worker:

   ```bash
   OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -m fitness.survey_worker --interval-seconds 900
   ```

   For the existing Docker Compose deployment, use `docker compose --profile survey up -d --build`. Set `DATABASE_URL` to the Compose database service hostname `database`, rather than `localhost`, and configure your public HTTPS reverse proxy. Run the survey worker instead of the older `learning` profile trainer; do not run parallel trainers against this development setup.
7. Run **connect** in Apps Script. It verifies the backend signature, imports exercise choices, installs submission and 15-minute reconciliation triggers, then publishes the form. Check the form's responder settings for your intended audience; Google Workspace policies may require sign-in.
8. Run **createParticipantLink** once per person. Copy that person's newest link from the spreadsheet's `_participants` tab. The code is prefilled; they do not need an app account or to invent an ID. Give the same person the same private link on later days. Do not share one link with a whole group. This function creates a link; it does not send it to anyone.
9. Submit one clearly identified pilot participant's real feedback, then run **reconcile** and **showTrainingStatus**. Check `_sync` for `active` or a retry/error status. Verify an edit and a withdrawal before wider collection. Retire the pilot participant through the withdrawal option if its data should not be retained.

The generic form URL is not sufficient for collection: unknown participant codes are rejected. Keep private links, the script and response spreadsheet accessible only to the organizer and the intended individual. Do not publish the response spreadsheet.

## What the participant sees

- A prefilled private participant code and an explicit consent/withdrawal choice.
- Workout date, workout number that day and exercise dropdown.
- Optional experience and readiness answers.
- Optional original planned reps, load and effort.
- Actual reps/load for the first set, optionally up to three sets, and optional effort/discomfort ratings.
- Optional enjoyment and whole-session duration.

No name, email, phone number, photo, injury narrative or medical diagnosis is requested. The form is a workout-feedback collector, not a clinical assessment or an anatomy-label crowdsourcing form. Declining to submit is always possible. Selecting withdrawal requires only the private participant link, not the workout pages.

Use the date in the configured timezone. Workout number distinguishes up to three separate sessions that day. This first survey records dates, not precise set timestamps or within-session exercise order. It supports one response per exercise per session and up to three sets with a common original prescription. Use the app's Contribute tab for more complex logs. Unknown optional answers remain unknown; they are not filled with invented targets.

The starter exercise dropdown uses existing dataset names. It does not prescribe these exercises, approve their safety metadata, or claim they suit every participant. Configure a manageable list for the exercises people actually perform. `refreshExercises` preserves old label mappings for historic responses. Keep the question titles and organizer sheet names intact because they define this version's import contract.

## When the AI updates

| Event | Automatic behavior after activation |
|---|---|
| New submission | Signed POST tries immediately; failed delivery remains retryable |
| Edit to an existing form response | Periodic scan detects its changed content and sends a higher revision |
| Delete in the Form's response store | Reconciliation removes the corresponding backend contribution and rebuilds affected learning data |
| Invalid edited answers | The script sends a deletion for the older training record; the form response remains available for correction |
| Consent withdrawal | Backend training records are erased and influenced models retired; the script also attempts to delete current Google Form responses, matching response-sheet rows and the stored private link |
| Eligible new data | Worker validates completeness, matching prescription and approved exercise metadata; it trains on changed eligible data when minimum split requirements are met |
| Candidate passes evaluation | Worker may deploy it in **shadow mode**: estimates are evaluated without altering prescribed workouts |
| Candidate is weak or data is insufficient | Existing rules remain available; no improved model is claimed |

The response **in Google Forms** is authoritative. Edit using the form's edit-response link. Direct edits/deletes in the linked Google Sheet are not imported and do not delete the corresponding Google Form response. The `_sync` sheet is an internal delivery journal, not a dataset editor; do not clear it or reset its revisions.

A 15-minute trigger is a requested schedule, not a real-time guarantee. Google quotas, outages, server availability, batching and training time may delay delivery. `reconcile` can be run manually for catch-up. Larger surveys are scanned in successive bounded runs. Check Apps Script execution failures, `_sync`, server health and worker logs rather than assuming that a saved Google response already changed weights.

The network being retrained predicts **RPE/difficulty from workout context**. Survey answers do not overwrite the source exercise classifier, muscle-function references or hard safety rules. Automatic validation is explicitly labeled as schema/completeness checks on self-reported data, not a qualified human review. The source exercise safety metadata still needs its normal qualified review; the default import remains `needs_review`, so that prerequisite can block training until resolved.

The existing learner needs at least 30 eligible sets and sufficient independent partitions to train an experimental candidate. Shared evaluation adds the existing 500-set/20-contributor and performance gates, plus longitudinal checks. These are engineering thresholds, not guarantees of statistical sufficiency, honest identities or clinical validity. A private participant link identifies a dataset contributor, not a verified human identity; issue only one link per participant.

## Changing actual workouts

Automatic candidate training and shadow updates are implemented. The worker deliberately preserves an existing live deployment and never promotes a candidate to live. The app remains a development build whose live training policy requires professional review. After reviewing a passing candidate, its shadow results and the release gates, an operator can use the existing command:

```bash
python -m fitness.ml activate MODEL_ID --mode live --reviewer REVIEWER --evidence REVIEW_REFERENCE
```

Do not fill those placeholders with fictitious approval. It is possible to automate live promotion later with a separately reviewed policy; this increment does not claim that policy has been validated.

## Security, corrections and recovery

- The HMAC covers the exact UTF-8 body, method, path, form ID, timestamp and nonce. Requests expire after five minutes, nonce replay is rejected, and response revisions prevent older retries from replacing new answers. HTTPS redirects are disabled so the bridge does not forward credentials to another origin.
- Only pre-enrolled random codes are accepted. Participant codes are hashed in the backend; the organizer's private Google link/response stores contain the original code. The shared webhook secret is held in Script Properties and backend environment settings.
- An ordinary new workout does not retire an already trained model. Corrections, deletions, relevant metadata changes and backdated history retire affected models and rebuild that contributor's derived examples chronologically. Raw source data and safety metadata are not automatically rewritten.
- The bridge cannot react to a remote change before Google delivers it. During a delivery outage, an edit or withdrawal has not yet reached the backend. An organizer can stop the survey, pause the worker and disable the deployed model while resolving an incident.
- Successful withdrawal purges current owned Google records as described above; copies, Google version history, independently exported files and backups require their own retention/reconciliation process. Backend restore revokes survey identities as well as existing API keys; fresh enrollment and consent are required.
- Run one worker for this development setup. High-volume queues, hosted PostgreSQL runtime verification, signed app builds, native survey usability, production monitoring, and full release/security reviews remain deployment tasks.

## Verification completed locally

The backend suite covers signature verification, replay/expiry, enrollment idempotency, consent, duplicate/reordered revisions, correction/delete invalidation, history rebuilding, participant isolation, incomplete/pain exclusions and metadata review changes. The JavaScript tests cover canonical request signing, missing answers, retry revisions, edits, invalid-edit removal and cleanup retries.

Google APIs were checked against official documentation, but the installer has **not been executed in a real Google account**. Live form creation, Google authorization, trigger delivery and public HTTPS behavior must be verified during activation. No form URL or active deployment is fabricated in this package.

References: [Google Forms service](https://developers.google.com/apps-script/reference/forms), [installable triggers](https://developers.google.com/apps-script/guides/triggers/installable), [form responses and prefilled links](https://developers.google.com/apps-script/reference/forms/form-response), [URL Fetch](https://developers.google.com/apps-script/reference/url-fetch/url-fetch-app).
