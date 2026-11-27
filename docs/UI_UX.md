# UI / UX specification

## Direction

A calm, premium training companion: forest background #101915, surfaces #1C2A23, lime action #D1F599, text #F1F5EE and secondary text #B5C3B9. Space and large typography prioritize a single next action. No stock athlete imagery or fabricated personal statistics.

## Screen system

| Screen | Primary task | Secondary content | Implemented limitations |
| --- | --- | --- | --- |
| Sign-in | Authenticate/create account | Clear minimum password length | Email verification/reset absent |
| Quick setup | Name, adult confirmation, goals/equipment/time | Total priority feedback | Four goals in UI, all goal types in API; schedule/experience editor pending |
| Today | Readiness and current session | Instructions, set logger, preparation/cooldown, sync state | Catalog approval required; full timer/coaching flow pending |
| Library | Search exercise text | Equipment and numbered instructions | First page only; Watch tutorial control, authenticated local GIF playback with play/stop and attribution |
| Progress | XP/level and logged session count | No punishment for rest | Charts and capability trends pending |
| Coach | Explain saved decisions | Clearly labeled rules mode | External LLM absent |
| Settings | Scoped key creation/revocation | Optional nutrition, sign-out | Full privacy/profile/preferences editor pending |

## Components and behavior

Buttons have a minimum 52px height, inputs 50px, tabs 48px. Native text remains scalable. Controls have screen-reader labels; tabs expose selected state; asynchronous status uses a polite live region. Layout wraps tabs on narrow devices. No custom motion is used, avoiding motion dependence. Text instructions accompany GIF tutorials and remain available when animations cannot load. Tutorials start only after an explicit tap, stop on backgrounding, and show Gym visual attribution. Secrets are selectable only immediately after creation and can be hidden.

Simple mode hides numerical ranking factors; advanced mode reveals stored reasoning and adjustment rationale. Permission-denied and unavailable integrations must explain availability without implying a disconnected feature works. Empty catalog state blocks prescription with a useful message rather than substituting a fake workout.

## Required device QA

VoiceOver/TalkBack focus order, 200% text, keyboard avoidance, Android back behavior, 320px widths, safe areas, dark-mode contrast measurement, screen rotation, offline startup, disconnect during set sync, low-memory restart, device clock changes and sign-out with pending logs. This has not been performed in this environment.

## Shared learning controls

Settings includes a separate Help improve training card. Contribution starts off. The card explains which data is used, presents an accessible switch, shows eligible and review-pending counts, and distinguishes rules, shadow evaluation and reviewed live assistance. Withdrawing asks for confirmation because it deletes learning examples and retires affected models; it does not delete workout history. Changes are confirmed by the server; failed/offline changes show an error and are not presented as saved.

Expandable details show how training works and the current user's account ID for historical import. Training is an operator workflow rather than a global control exposed to ordinary users. No fabricated accuracy, "learning" animation or trained-model claim is shown before a candidate exists. Existing advanced workout reasoning shows model version, predicted RPE at the original load and any bounded adjustment.

## Contribute tab

The new primary tab follows Check-in → Exercise and sets → Review and send. Choice controls have explicit radio labels, selected state, scalable text and 48px minimum targets. Unknown answers are first-class options. Stepper controls supplement direct number entry. The exercise picker shows name and equipment; no identifier is exposed to participants. Copy-last-set resets actual effort and pain. The receipt translates completeness reasons into plain language and makes reviewed/awaiting-review states visible.

A contribution can include one exercise with multiple sets. Add another exercise preserves the workout grouping and check-in. Optional context/plan details explain why a record may not be model-ready. Enjoyment/duration are collected as optional observations, not claimed as trained model inputs. The owner dashboard is currently CLI based. Native screen-reader, keyboard, large-text and device walkthrough checks remain required before public distribution.

Ordinary workout logging also gains reps/load steppers and explicit actual-effort selection. Onboarding asks users to choose their experience rather than assigning beginner status silently.
