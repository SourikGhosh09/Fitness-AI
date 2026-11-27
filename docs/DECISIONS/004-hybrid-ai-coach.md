# 004 Hybrid AI coach

Status: accepted for milestone 1 (user-approved scope, 2026-11-27).

- The deterministic engine stays the source of truth for loads, swaps, readiness and pain. The language model only talks and proposes.
- Local first: a ~1.5B instruction model (4-bit weights) runs on the phone through react-native-executorch. It is downloaded once, only after the user confirms, and can be turned off.
- Cloud second, opt-in: heavy questions can go to a free-tier hosted model through the backend. The app never holds a provider key. The user switch is off by default because free tiers may retain prompts.
- Pain and emergency wording never reaches a model. It gets a fixed reply (app and server).
- Model output is untrusted input. An action line is parsed, range-checked and shown as a confirm card. Applying it calls the same endpoints as the buttons, so engine validation, ownership checks and the offline set queue still apply.
- Not validated on real devices yet. Report phone RAM, speed and answer quality before widening scope.
