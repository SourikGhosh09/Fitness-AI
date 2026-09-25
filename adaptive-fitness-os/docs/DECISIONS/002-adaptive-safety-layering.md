# ADR 002 — Adaptive intelligence remains subordinate to deterministic safety

**Status:** Accepted  
**Date:** 2026-09-25

## Context
Fitness AI combines rules, history and experimental learned RPE prediction.

## Decision
Deterministic eligibility/safety runs before adaptive ranking or ML. Learned behavior may annotate or conservatively reduce an eligible prescription within reviewed bounds and is followed by safety validation.

## Consequences
No model/coach feature may directly bypass restrictions, pain stops, metadata approval, equipment or authorization. Adaptive decisions remain auditable and reversible.
