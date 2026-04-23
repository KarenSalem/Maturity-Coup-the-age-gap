# ATUS Microdata Plan

## Goal
- Build a true age series for socializing and communicating, centered on `15-19` and `20-24`, with older age groups as comparators.
- Keep `2020` as a visible gap / disruption year when annual estimates are unavailable.

## Source Files
- Annual ATUS activity-summary files: 2014 through 2024
- Optional support files: respondent, who, and ATUS-CPS files if needed for validation

## Core Fields
- `TEAGE`
- `TESEX`
- `TUFINLWGT`
- activity-summary minutes for socializing and communicating
- minutes spent alone or with others if the measure can be derived from the who file

## Intended Outputs
- `atus/socializing-by-age-history.csv`
- `atus/atus-socializing-age-history.svg`
- Optional companion: `atus/alone-with-others-history.csv` and SVG

## Guardrails
- Prefer published BLS tables for stopgaps.
- Use microdata only for the age series that the public tables do not provide cleanly.
- Keep the output framed as social connection / time alone, not emotional well-being.
