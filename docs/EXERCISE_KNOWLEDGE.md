# Initial exercise knowledge and neural training

This package includes **trained weights**, not an empty model scaffold. It works without ChatGPT, an external AI provider, an API credit balance or participant data. A running Fitness OS backend is still required by the mobile app.

## Try it

After the normal backend setup and mobile startup in the README:

1. Open **Coach** and tap **What do biceps do?** or **Which exercise comes first?**
2. Open **Library**, search for an exact exercise and tap **What this exercise targets**. Its existing animation and original instructions remain available.
3. In Coach, expand **Explore the trained neural model**, then enter an exercise name. Predictions are explicitly experimental. An uncertain result asks you to choose the exact exercise in Library.

The initial source contains 1,324 exercises and 19 target categories. Categories include broad regions and `cardiovascular system`; `spine` is explicitly identified as a source region label, not a muscle.

## Three distinct capabilities

| Capability | How it works | Authority and limits |
|---|---|---|
| Exact exercise targets and tutorials | Read original imported exercise records | Reports the dataset's claims with record provenance; does not invent activation percentages or suitability |
| Muscle functions | Short sourced educational entries in `data/knowledge/muscles-and-order.json` | Original AI-assisted summaries pending qualified review; no personalized diagnosis |
| Target-category suggestions | Trained name classifier, a 64-unit tanh neural layer followed by 19-way softmax | Experimental name-to-source-label prediction; never overrides exact source facts or safety |
| Exercise order | Explicit goal-priority rules after approved exercise selection, followed by saved order explanations | Not trained from the source because it has no measured optimal-order outcomes |

The existing **RPE prediction network** is separate. It still needs consented, quality-controlled participant outcomes. Training the exercise classifier does not create a real-user response model, clinical validation or general conversational intelligence.

## Actual training run

The source snapshot is commit `7455efae41b330c265e7cd4b78dfa848e7ce5ebd`, SHA-256 `656634224b8977b99a6d765470ee123260d4979715eaa4e7c0b7c8bb0d79f93d`.

- Training: **916** exercise records.
- Validation: **219** records, used for early stopping.
- Test: **189** records, held out from optimization and model selection.
- Held-out top-1 source-label accuracy: **70.9%**.
- Macro F1 over classes represented in the test set: **0.590**.
- Nearest training-name baseline: **59.8%**; training-majority-label baseline: **9.0%**.
- The fixed suggestion gate displayed a suggestion for **97/189** test names (51.3% coverage), with **89/97** agreeing with source labels. This conditional result is not overall accuracy or clinical confidence.
- The chosen checkpoint is epoch **16**, using seed 42.

See `data/knowledge/training-report.json` for partition IDs, class support/F1, loss history, baselines and suggestion coverage. Rare categories are weak or untested. For example, hamstrings and cardiovascular-system categories have zero test F1 in this run. These results are not accuracy measurements of anatomical understanding or workout quality.

Equipment/position variants are grouped before a deterministic hash split to reduce variant leakage. This is a text heuristic and cannot prove that every related exercise family is separated. The word/bigram vocabulary is fitted only on training names. The input excludes target fields, secondary muscles, IDs, instructions and media. Labels define the output category vocabulary; absent training classes are not magically learned.

Training uses real backpropagation, class-weighted cross-entropy, mini-batch Adam and validation early stopping. The weights are plain JSON numeric arrays, not executable pickle files. Raw softmax scores are **not calibrated probabilities**. Word coverage, score margin and training-support thresholds limit when suggestions are displayed; they are engineering heuristics, not clinical confidence measures. Held-out results were not used to tune these thresholds.

## Retrain independently

From `backend` with the project's Python environment active:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -m fitness.knowledge_model
```

This regenerates the source-only model and report in `data/knowledge`. No user data, textbook prose or animations enter training. It does not overwrite the exercise dataset, approve exercise safety metadata or activate the RPE model.

For an operator-controlled experiment on a separate exercise dataset:

```bash
python -m fitness.knowledge_model --source /absolute/path/exercises.json --output /absolute/path/experiment
```

Each record must have a unique `id`, `name` and `target`. Use meaningful, reviewed labels and enough distinct exercise families. Keep private participant records out of this source-only artifact pipeline. The participant consent and review workflow is documented in `TRAINING.md` and `COLLECTING_DATA.md`.

For additional examples, maintain a versioned extension dataset separately from the original supplied files. Prepare its reviewed names/targets as an operator training export. The running backend only serves a bundled classifier when its source SHA matches the configured source dataset and its model checksum matches its report. Do not replace only one of these files. Stop the backend while promoting a tested model/report pair; retain the previous pair for rollback. The source/report pairing is an integrity check, not a cryptographic signature against an attacker who controls deployment files.

Correct anatomy summaries in `muscles-and-order.json`, recording the reference and reviewer. Those summaries are **not** automatically converted into training labels. Changing definitions, accepting crowd edits, or collecting more user logs does not automatically improve a network. Review the data, retrain, evaluate and compare the candidate before promoting it.

## Ordering rationale

The ACSM 2026 review reports that strength development can favor exercises placed early in a session. The 2010 Simao trial also supports considering the priority exercise first rather than always starting with the largest muscle. Neither source provides a universally optimal sequence for every person and goal.

The app's explicit resistance-session policy is readiness → specific preparation → priority work → supporting work → optional goal-appropriate conditioning → cooldown/feedback. In generated main work, already-approved exercises are ordered by reviewed goal compatibility, then technical demand, with original order retained for ties. Each item records its order rationale. This does not infer power suitability or medical clearance from an exercise name. The engine's broader cardio, periodization and full warm-up limitations remain as documented in `FEATURE_STATUS.md`.

A knowledge answer never changes an existing workout. The order endpoint lists the most recently saved plan and labels it as saved main work. It is not a new recommendation or a promise that the saved plan is appropriate to perform now; readiness and safety gates still run through the normal workout path.

## References and provenance

- [Original exercise source](https://github.com/hasaneyldrm/exercises-dataset/tree/7455efae41b330c265e7cd4b78dfa848e7ce5ebd). User-supplied data and owner-authorized media; original notices are retained. See `LICENSING.md` and `ANIMATED_TUTORIALS.md`.
- OpenStax, Betts et al., *Anatomy and Physiology 2e*: [upper limb](https://openstax.org/books/anatomy-and-physiology-2e/pages/11-5-muscles-of-the-pectoral-girdle-and-upper-limbs), [lower limb](https://openstax.org/books/anatomy-and-physiology-2e/pages/11-6-appendicular-muscles-of-the-pelvic-girdle-and-lower-limbs), [abdominal wall](https://openstax.org/books/anatomy-and-physiology-2e/pages/11-4-axial-muscles-of-the-abdominal-wall-and-thorax), [back](https://openstax.org/books/anatomy-and-physiology-2e/pages/11-3-axial-muscles-of-the-head-neck-and-back). Access for free at https://openstax.org/books/anatomy-and-physiology-2e/pages/1-introduction. Brief original factual summaries are provided with references; no textbook chapters or textbook-derived neural training corpus are included.
- [ACSM 2026 resistance training position stand](https://pmc.ncbi.nlm.nih.gov/articles/PMC12965823/).
- [Simao et al. 2010, Influence of Exercise Order](https://pmc.ncbi.nlm.nih.gov/articles/PMC3737971/).

## Read-only API

Authenticated `/api/v1` routes:

- `GET /knowledge/status`: verified model state and evaluation summary.
- `GET /knowledge/muscles` and `?q=biceps`: category index and sourced function.
- `GET /exercises/{exercise_id}/knowledge`: exact source targets and associated function.
- `GET /knowledge/order`: stage policy and owner-isolated saved main-work order.
- `GET /knowledge/classify?name=dumbbell%20concentration%20curl`: experimental suggestion or abstention.
- `POST /coach`: bounded knowledge intents, with symptoms taking priority.

The model is disabled on missing/corrupt files or a changed source dataset. Known-source lookup remains independent. These routes add no personal-data table or consent change, so no database migration is needed for this feature.
