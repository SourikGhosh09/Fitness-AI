# Product requirements

## Outcome

Support the loop assess → plan → prepare → train → measure → recover → adapt. Users should quickly understand today's action, its duration, readiness, and why programming changed. The source of truth is durable application state. Coaching must not manufacture that state.

## Audience and scope

The long-term target spans adult beginners through competitive athletes and concurrent goals. This development implementation provides an adult quick-setup path and experimental general resistance programming. It must not be positioned as validated competitive sport, injury rehabilitation, pediatric, pregnancy or clinical nutrition software.

Required inputs: adult confirmation, display name, weighted goals, equipment, schedule/duration. Email/password are required for remote account access. Optional: age, sex, height, weight, body fat, sport, training history, activity level, preferences, injuries, restrictions and nutrition. Request optional permissions only when a feature is explicitly enabled.

## User journeys and acceptance criteria

| Journey | Acceptance criteria |
| --- | --- |
| Onboard | Goal priorities total 100%; optional sensitive fields can be omitted; camera/wearables not required |
| Prepare | Recent readiness required; pain/alarming symptoms block auto-prescription; no eligible catalog returns an explanation |
| Train | Explain exercise choice; show instructions, sets/reps/RPE/rest; log actual results or explicit skips |
| Substitute | Preserve movement intent; re-filter equipment and safety; discard old exercise load; discomfort pauses first |
| Offline | Save pending set events durably; stable event ID across retries; conflicting writes retained for review |
| Adapt | Require three distinct completed sessions before a small load adjustment; log engine version and reasoning |
| Recover | Rest sessions receive recognition; no XP loss or attack penalties; unfinished sessions cannot award repeated XP |
| Developer access | Create scoped expiring key, reveal once, list without secret, revoke immediately |
| Privacy | Account export and deletion; credentials excluded; device cache cleared on sign-out |

## Full requested product roadmap

1. Validate exercise metadata and training policy with qualified reviewers; complete guided assessments and capability estimates with confidence, date, source and uncertainty.
2. Implement full multi-domain concurrent programming: explicit cardio/mobility allocation, power and sport specificity, individualized volume, periodization, deload and progressions beyond the initial load heuristic.
3. Add nutrition trends, food/allergy matching, meal suggestions, hydration and appropriate screening.
4. Integrate optional native health adapters; normalize units, source, permissions, timestamps, duplicate signals and trend quality.
5. Implement opt-in on-device camera pipeline with confidence rejection, occlusion detection and evaluated per-exercise performance.
6. Add provider-backed conversational intent extraction using validated tool contracts and narrow authorization. Mutations require the same application safety checks as direct UI actions.
7. Introduce ML only after consented, sufficient, labeled longitudinal data; compare held-out outcomes with the deterministic baseline before rollout.

## Success measures

Track opt-in activation, session completion, logging burden, consistency, useful substitutions and user-rated explanation clarity. Track inappropriate recommendations, pain-pause failures, privacy incidents and stale/offline errors as release-stopping outcomes. Do not optimize total training volume or compulsive engagement as product success metrics.

## Release acceptance

All production gates in PRODUCTION.md must close before describing the product as production-grade. The full feature-status matrix is the binding record of implementation completeness.
