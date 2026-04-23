# AGENTS.md

## Current Goal

Build a linkable, high-end data package around this thesis:

today's 18-year-olds are the least autonomous generation in American history, not because of the pandemic but because we stopped letting them grow up.

## Source Map

### Licensed Drivers by Sex and Age Groups, 1963-2024
- Source CSV: https://data.transportation.gov/api/views/jm62-yva2/rows.csv?accessType=DOWNLOAD
- Dataset page: https://data.transportation.gov/Roadways-and-Bridges/Licensed-Drivers-by-Sex-and-Age-Groups-1963-2024-D/jm62-yva2/about_data
- Fields used: year, sex, age group, licensed-driver counts
- DL-20 rate tables used: 2010, 2012, 2014, 2016, 2018, 2020, 2022, 2024
- Fields used there: age group, drivers as percent of age-group population, by sex and total

### BLS Teen and Youth Labor Force Data
- Teen annual LFPR series: https://www.bls.gov/opub/mlr/2017/article/teen-labor-force-participation-before-and-after-the-great-recession.htm
- July youth LFPR series, ages 16-24: https://www.bls.gov/opub/ted/2024/youth-labor-force-participation-rate-at-60-4-percent-in-july-2024.htm
- CPS monthly age table A-8b: https://www.bls.gov/web/empsit/cpseea08b.htm
- Employment Projections table 3.3: https://www.bls.gov/emp/tables/civilian-labor-force-participation-rate.htm
- Fields used: teen annual LFPR, July youth LFPR, monthly 16-19 LFPR, A-8b age splits (16-17, 18-19, 20-24, 25-54), age-specific participation rates
- Local A-8b history file: `bls/a8b-age-split-history.csv`

### ATUS Social Connection
- ATUS overview: https://www.bls.gov/tus/overview.htm
- ATUS leisure-by-age chart: https://www.bls.gov/charts/american-time-use/activity-leisure.htm
- ATUS waking-hours table A-8: https://www.bls.gov/tus/tables/a8-2024.pdf
- Fields used: socializing and communicating by age, waking hours alone, waking hours with others present
- Local extracts: `atus/socializing-by-age-2024.csv`, `atus/alone-with-others-2024.csv`
- Microdata target: annual 2014-2024 activity-summary files for age-specific socializing and communicating
- 2020 ATUS annual estimates are a known gap because the survey was suspended during the pandemic

### Census Living Arrangements of Young Adults
- Historical Living Arrangements of Adults table page: https://www.census.gov/data/tables/time-series/demo/families/adults.html
- AD-1 table: young adults 18-34 living at home, 1960 to present
- AD-3 tables: adults 18+ and age-group cuts for 18-24 and 25-34
- Figure AD-1 / related story: young adults living in the parental home, with decennial 1960-1980 and CPS ASEC 1983-2023 coverage
- Fields used: year, sex, age band, living-in-parental-home share, living arrangement category
- Local extracts: `census/ad1-living-at-home.csv`, `census/census-ad1-longtrend.svg`

## Working Rules

- Canonical source folders are `licensed-drivers/` and `bls/`.
- Add `census/` as the household-independence source folder.
- Add `atus/` as the social-connection source folder.
- Treat files in those folders as the source of truth for the current package state.
- Keep the licensed-driver and BLS packages separate unless a later task explicitly asks to connect them.
- Treat that separation as a working rule, not the project objective.
- Keep `18` as the anchor age unless a source-specific reason clearly points elsewhere.
- When building new trend series, pull back to at least `2014` when the source coverage allows it.
- Prefer the AD-1 long trend over the benchmark slopegraph when the goal is to show the household-independence arc.
- Use ATUS as a support layer for social connection and time alone, not as a loneliness claim.
- For ATUS, prefer microdata for true age series; use published tables only as stopgaps.
- Prefer concise, newsroom-style data presentation.
- Verify source tables or series before using them in new charts or claims.
- Reuse existing generated assets when updating visuals; do not rebuild from scratch unless necessary.
