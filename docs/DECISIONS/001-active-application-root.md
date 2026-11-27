# ADR 001 — Active application root

**Status:** Accepted  
**Date:** 2026-09-25

## Context
The distributed repository contains older duplicated application files in the parent tree and a newer, more complete implementation in `adaptive-fitness-os/`.

## Decision
Treat `adaptive-fitness-os/` as the source of truth for new Fitness AI development. Legacy copies are not modified except during an explicit migration/removal task.

## Consequences
Agents must verify paths before editing. Documentation/control files maintained here describe the active implementation. A future cleanup may remove or archive duplicates after validation.
