# User Flows

## Onboarding
Register/sign in → confirm adult scope → set goals/equipment/schedule → optional personal fields/consents → save profile → Today/Plan. Invalid goal totals or unsupported safety conditions block automatic prescription with an explanation.

## Daily training
Open Today → submit readiness → safety evaluation → generate/retrieve plan → inspect exercises and reasons → start → log each set/skip/pain → complete → history/progress updates → eligible consented outcomes may enter learning pipeline. Pain/alarming symptoms pause or block automatic programming.


## Adaptive week
Open Plan → fetch derived current week → view training/rest/completed/missed/upcoming states → if a tracked scheduled session was missed, earliest unfinished sequence slot is carried to the next available training day → recovery snapshot shows completed-session recency/set-equivalents → Today uses that day template when generating the session. A new user with no prior history does not receive invented missed-day penalties.

## Regenerate workout
Open an active unstarted training workout → choose regeneration reason (variety, equipment, time, fatigue) → system reuses the weekly session intent and reruns all safety/catalog/history/volume logic → stores a new workout snapshot version and decision record. If any set has been logged, regeneration is rejected; individual same-pattern replacement remains the safe edit path.

## Replace exercise
From active plan choose Replace → system preserves movement intent and re-applies equipment/safety/review filters → replacement receives a fresh prescription; old exercise load is not blindly copied.

## Offline logging
Log set → persist local event with stable ID → attempt sync → retry safely → server deduplicates; conflicts remain visible/pending rather than silently overwritten.

## Contribution/learning
Explicit opt-in → enter/import outcome → validation/review → eligible examples → candidate training → shadow evaluation → reviewed deployment only after gates. Withdrawal stops collection and invalidates affected learning artifacts as documented.

## Account/data
Profile/Settings → export, API keys, integrations/consent, or delete account. Authorization always resolves ownership from authenticated credentials.
