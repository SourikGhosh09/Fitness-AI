# UI Specification — Evolve v0.3.1

## Design direction
Original dark fitness interface inspired by modern training apps without copying a specific product: near-black canvas, graphite cards, restrained electric-blue accent, strong hierarchy, large touch targets and clear adaptive explanations.

## Navigation
Primary information architecture: **Today · Plan · Log · Exercises · Progress · Profile**, with Coach accessible contextually/within the product navigation as implemented.

## Major experiences
**Today:** readiness, recovery/fatigue state, today's session, duration/muscle focus, primary Start action. **Plan:** seven dated cards for training/rest/completed/missed/upcoming states, carry-forward explanation, readiness summary and completed-history recovery-recency snapshot. **Workout:** exercise media, sets, rep range, load, RPE/RIR, rest, target muscles, Why this?, Replace/Edit where safe. **Exercises:** search/filter library and GIF tutorials. **Progress:** strength/body-weight/volume/consistency/recovery/progression trends. **Profile:** goals, equipment, schedule, assessment, consent, integrations, export/security/settings.

All displayed prescription values must come from backend state or be explicitly labeled estimates. Loading, empty, offline, validation and safety-blocked states must be distinguishable. Support scalable text, screen-reader labels and comfortable touch targets.

## Evolve interactions

Onboarding and Profile expose a seven-day availability picker. Saving changed days updates the profile, invalidates an unstarted server workout through existing profile behavior, clears stale local Today cache and reloads the derived week.

Today uses the weekly template title as the session title. Carry-over sessions show the reason. Before logging begins, users can request **Regenerate variety** or **Make it lighter**; started sessions cannot be silently rewritten. The UI must continue to label readiness/recovery/workload values as heuristic planning support, not medical measurements.

## Log tab
Monday-Sunday date strip (status dot per day), previous/next week, jump to a date and Today. Each day shows session time (start, pause, resume, finish), set-by-set weight, reps or seconds and RIR with a Done control, a rest countdown that starts when a set is ticked (adjust by 15 seconds or skip), a countdown for timed sets, last-time hints, warm-up, stretch and cooldown checklists, conditioning, review fields and Share. Each catalog exercise has Show tutorial, which starts its animation in place; custom exercises show that no tutorial exists. Every control has an accessibility label and numeric fields are never silently converted from blank to zero. Edits save on this device first and sync automatically.
