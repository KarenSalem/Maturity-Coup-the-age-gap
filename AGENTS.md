# AGENTS.md

## Current Goal

Build a linkable, high-end data package around this thesis:

today's 18-year-olds are the least autonomous generation in American history, not because of the pandemic but because we stopped letting them grow up.

## Source Map

### Licensed Drivers by Sex and Age Groups, 1963-2024
- Source CSV: https://data.transportation.gov/api/views/jm62-yva2/rows.csv?accessType=DOWNLOAD
- Dataset page: https://data.transportation.gov/Roadways-and-Bridges/Licensed-Drivers-by-Sex-and-Age-Groups-1963-2024-D/jm62-yva2/about_data
- Fields used: year, sex, age group, licensed-driver counts

### BLS Teen and Youth Labor Force Data
- Teen annual LFPR series: https://www.bls.gov/opub/mlr/2017/article/teen-labor-force-participation-before-and-after-the-great-recession.htm
- July youth LFPR series, ages 16-24: https://www.bls.gov/opub/ted/2024/youth-labor-force-participation-rate-at-60-4-percent-in-july-2024.htm
- CPS monthly age table A-8b: https://www.bls.gov/web/empsit/cpseea08b.htm
- Employment Projections table 3.3: https://www.bls.gov/emp/tables/civilian-labor-force-participation-rate.htm
- Fields used: teen annual LFPR, July youth LFPR, monthly 16-19 LFPR, age-specific participation rates

## Working Rules

- Canonical source folders are `licensed-drivers/` and `bls/`.
- Treat files in those folders as the source of truth for the current package state.
- Keep the licensed-driver and BLS packages separate unless a later task explicitly asks to connect them.
- Treat that separation as a working rule, not the project objective.
- Prefer concise, newsroom-style data presentation.
- Verify source tables or series before using them in new charts or claims.
- Reuse existing generated assets when updating visuals; do not rebuild from scratch unless necessary.
