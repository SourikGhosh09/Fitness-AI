# Feature Inventory

| Area | User value | Current status | Next work |
|---|---|---|---|
| Account/profile/goals | Personalized durable state | Implemented foundation | richer assessments |
| Readiness & safety | Prevent inappropriate automatic training | Implemented deterministic fail-closed core | validation/reviewer refinement |
| Adaptive workout planning | Actionable personalized sessions | **Evolve weekly planner implemented**: schedule-aware split, missed-session carry-forward, day-specific pattern intent | periodization and richer multi-domain scheduling |
| Progression | Progressive overload with explanations | Rep ranges/load adaptation + safe pre-logging regeneration implemented | richer strategy selection/volume constraints |
| Exercise library/tutorials | Discover and perform movements | 1,324 catalog + authenticated media | device UX validation |
| Logging/offline | Reliable training history | implemented cache/outbox foundation | reconciliation/native QA |
| Progress/reporting | Understand trends | foundation + adaptive summaries | richer longitudinal charts |
| Coach/knowledge | Explain exercises/programming | bounded rules + trained name classifier | optional narrow intent adapter later |
| Learning/RPE model | Learn difficulty from consented outcomes | pipeline implemented; no validated real-user model bundled | real-user shadow evaluation |
| Notion/contributions | Collect consented participant data | implemented/local validation | hosted activation |
| Nutrition | Optional approximate planning | basic macros | trends/meals/hydration |
| Wearables/camera | Optional automated signals | not implemented | future opt-in adapters |

Detailed binding status remains `FEATURE_STATUS.md`; speculative/future items are not claims of implementation.

### Evolve v0.3.0 acceptance

- Weekly plan returns seven dated day states and an explainable next session.
- 5-day availability maps to Upper A / Lower A / Full Body / Upper B / Lower B; other frequencies use bounded supported templates.
- Once tracking exists, an uncompleted past scheduled day is marked missed and its earliest unfinished slot moves to the next available day.
- A brand-new user is not assigned fabricated misses for days before the first observed session.
- Day-specific workout generation only selects patterns from the assigned template and still applies readiness, safety, volume, exercise review and equipment filters.
- Regeneration is blocked after set logging starts and is recorded as a versioned recommendation decision.
