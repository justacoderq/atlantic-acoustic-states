# Animal data audit

Reproduce with `python scripts/audit_animals.py` from the repository root. It
writes three tables to `results/tables/`:

- `animal_audit_files.csv`: one row per NetCDF file, with metadata and checks
- `animal_coverage_units.csv`: species × deployment, in native units
- `animal_presence_native.csv`: presence summary per species

## Summary

- **`animals.csv` matches the 105 NetCDF files.** Every daily and hourly
  presence value in the CSV equals the source file. No CSV file is missing a
  NetCDF, and no NetCDF is missing from the CSV.
- **Every species was put on the acoustic hourly grid.** For each deployment,
  the CSV has one row per hour that has acoustic data. Daily products were
  repeated across the 24 hours of each UTC day. So the 17,577 "daily" rows
  per whale species are really **745 days**. For daily comparisons, collapse
  to one row per day first (`time.dt.floor("D")`).
- **Cod is not a regular time series.** The NetCDF is a list of individual
  grunts (about 0.1 to 1 s each). The CSV's hourly 0/1 values were made by our
  pipeline: 1 if any grunt started in that hour, otherwise 0. That is our own
  preprocessing step, not a NOAA product.
- **Blue whale has 0 detections in all 745 days.** This is a real "analyzed,
  not detected" result, not missing data. The metadata describes the manual
  review method used for blue whales. With no positive days, it can't be
  related to anything.
- **Coverage is uneven** (table below). Dolphins cover all 18 deployments.
  Fin, humpback, right, sei, and blue whale stop after SB01_12 (2020-11-22).
  Minke stops after SB01_15. Cod is missing SB01_10, SB01_11, and SB01_15 to
  SB01_18.

## Products

All files are NOAA-Navy SanctSound detection products from site SB01
(42.4368 N, 70.5470 W, SoundTrap ST300), created 2022-08-22. Each file has its
own DOI in the `id` attribute (copied to `animal_audit_files.csv`). Times are
UTC, stored as `start_time`/`end_time` in milliseconds since 1970. Presence is
0 = not present, 1 = present.

| Species | NetCDF product | Method (from metadata) | Native unit | Deployments | Units | Present | % |
|---|---|---|---|---:|---:|---:|---:|
| Humpback whale | `_1d` | LFDCS detector + manual daily review | UTC day | 12 | 745 | 424 | 56.9 |
| Fin whale | `_1d` | LFDCS + manual review | UTC day | 12 | 745 | 232 | 31.1 |
| Minke whale | `_1d` | XBAT pulse-train detector + analyst daily review | UTC day | 15 | 930 | 127 | 13.7 |
| Sei whale | `_1d` | LFDCS + manual review | UTC day | 12 | 745 | 101 | 13.6 |
| N. Atlantic right whale | `_1d` | LFDCS + manual review | UTC day | 12 | 745 | 51 | 6.8 |
| Blue whale | `_1d` | LFDCS (MD ≤ 5.0) + manual review | UTC day | 12 | 745 | 0 | 0.0 |
| Dolphins | `_1h` | PAMGuard whistle/moan detection | UTC hour | 18 | 26,842 | 5,020 | 18.7 |
| Atlantic cod | events (no suffix) | automatic grunt detector + manual verification | individual grunts → binned by us to hours | 12 | 18,106 h | 429 h | 2.4 |

"Units" counts only days or hours that also have acoustic data.

## Coverage (native units per deployment)

Daily species are counted in days; dolphins and cod in hours. 0 means no
product for that deployment.

| Deployment | Dates | Cod (h) | Dolphins (h) | Blue/Fin/Humpback/Right/Sei (d) | Minke (d) |
|---|---|---:|---:|---:|---:|
| SB01_01 | 2018-11-12 → 2019-01-28 | 1846 | 1846 | 78 | 78 |
| SB01_02 | 2019-01-28 → 2019-04-02 | 1531 | 1531 | 65 | 65 |
| SB01_03 | 2019-04-10 → 2019-06-01 | 1260 | 1259 | 53 | 53 |
| SB01_04 | 2019-06-01 → 2019-08-02 | 1487 | 1487 | 63 | 63 |
| SB01_05 | 2019-08-02 → 2019-10-05 | 1532 | 1532 | 65 | 65 |
| SB01_06 | 2019-10-05 → 2019-12-06 | 1486 | 1486 | 63 | 63 |
| SB01_07 | 2019-12-06 → 2020-01-31 | 1340 | 1340 | 57 | 54 |
| SB01_08 | 2020-01-31 → 2020-04-07 | 1608 | 1607 | 68 | 68 |
| SB01_09 | 2020-04-07 → 2020-06-12 | 1581 | 1581 | 67 | 67 |
| SB01_10 | 2020-06-12 → 2020-08-14 | 0 | 1508 | 64 | 64 |
| SB01_11 | 2020-08-14 → 2020-09-17 | 0 | 813 | 35 | 35 |
| SB01_12 | 2020-09-17 → 2020-11-22 | 1584 | 1583 | 67 | 67 |
| SB01_13 | 2020-11-22 → 2021-01-26 | 1559 | 1559 | 0 | 66 |
| SB01_14 | 2021-01-26 → 2021-03-21 | 1292 | 1268 | 0 | 54 |
| SB01_15 | 2021-03-21 → 2021-05-27 | 0 | 1600 | 0 | 68 |
| SB01_16 | 2021-05-27 → 2021-07-27 | 0 | 1464 | 0 | 0 |
| SB01_17 | 2021-07-27 → 2021-09-25 | 0 | 1437 | 0 | 0 |
| SB01_18 | 2021-09-25 → 2021-12-15 | 0 | 1941 | 0 | 0 |

Dates are the acoustic coverage per deployment, from `all.csv`.

## Details and minor issues

- **Detections with no acoustic data were dropped (expected).** The CSV only
  keeps hours that have acoustic data, so these were left out: 45 daily units,
  213 dolphin hours, and 2 cod grunts. Most of this is one stretch, below. It
  doesn't affect our analysis, because we can only compare animals to acoustic
  states where acoustic data exist.
- **SB01_03 animal files start 8 days before the acoustic data.** The animal
  products start 2019-04-02, but the acoustic data, and the metadata's own
  "recorded between April 10 and June 01" text, start 2019-04-10. Those 8 days
  include real detections (61 dolphin hours, 1 humpback day). It's unclear
  whether only the sound-level product is missing that week or the metadata
  text is wrong. Not resolved; the CSV excludes these days either way.
- **Cod "no detections" placeholders.** SB01_03 and SB01_14 each contain one
  record spanning the whole deployment with presence 0, meaning analyzed with
  no grunts found. The CSV correctly shows 0 for every hour.
- **Cod SB01_07 has 19 records with presence 0** mixed in with its grunts.
  These look like reviewed, rejected detections. The CSV correctly ignores
  them.
- **Cod SB01_04's only record is dated 2019-03-23**, outside SB01_04's
  June–August 2019 recording period (it falls during SB01_02). It looks like a
  placeholder or a metadata error. The CSV shows SB01_04 with no cod, which is
  likely correct, but it isn't confirmed.
- **Cod is sparse and clumped.** 429 present hours, mostly in SB01_01, 06, 07,
  12, and 13 (the autumn and winter deployments). Grunts per present hour: median
  1 to 2, max 28.
- **Dolphins SB01_14 is missing all of 2021-01-29** (24 hours). Acoustic data
  exist for that day, so it isn't in the CSV and those hours have no dolphin
  value. Every other hourly and daily product is a regular grid.
- **Data-quality comments.** Most files say "quality data for the duration of
  the deployment." SB01_01 reports two short recording gaps (2019-01-27
  11:28–14:26 and 2019-01-28 08:26–10:19 UTC) that overlap 7 acoustic hours.
  All SB01_06 files report a 2-minute gap on 2019-10-30. Neither matters at hourly or
  daily resolution.
- **Boundary days appear in two deployments.** On the day one deployment
  ends and the next begins, both daily products cover that UTC date, and each
  assessed only its own part of the day. Across species this affects 61
  species-days, and the two disagree on 9. `scripts/build_animal_tables.py`
  merges them into one row per UTC date: present if either part had a
  detection, with the acoustic hours of both parts added together.
- **Partial days.** Deployment boundaries create 22 UTC days with fewer than
  24 acoustic hours. 19 of them have 20 to 23 hours; only 3 have fewer than 20.
  Within the whale window, only 2018-11-12 and 2019-04-02 fall below 20 hours. A daily state summary for those days is
  based on fewer hours.

## Open items

- **Question for the team: blue whale.** It has 0 detections in 745 analyzed
  days. Drop it from the comparisons and report it as "not detected" in the
  data description?
  - Prachi:
  - Jacob: Drop it from the comparisons and report it as analyzed but not
    detected in the data description.
  - Parker:
  - Decision: Drop blue whale from the comparisons; report it as analyzed but
    not detected.
- **Question for the team: partial days.** For the daily animal vs. state
  comparison, should we require a minimum number of acoustic hours per day
  (for example, at least 20 of 24), or keep all days? Requiring at least 20
  hours drops 3 days (2018-11-12, 5 h; 2019-04-02, 13 h; 2021-12-15, 16 h), 2
  of them in the whale window. Requiring all 24 hours drops 22 days.
  - Prachi:
  - Jacob: Require at least 20 acoustic hours per day.
  - Parker:
  - Decision: Require at least 20 acoustic hours per day (`keep_day` in
    `data/processed/animals_daily.csv`).
- **Question for the team: cod.** The hourly values are our own binning of the
  grunt events. Keep cod as an hourly presence series (like dolphins), or
  leave it out because it's so sparse (2.4% of hours, missing 6 of 18
  deployments)?
  - Prachi:
  - Jacob: Keep it hourly, like dolphins, but label the hourly presence as our
    own derived binning and note that results rest on few hours.
  - Parker:
  - Decision: Keep cod hourly, labelled as our own derived binning
    (`derived_binning` in `data/processed/animals_hourly.csv`), and note that
    cod results rest on few hours.
- **Comparison window.** Whale comparisons can only use SB01_01–SB01_12
  (Nov 2018 – Nov 2020), extended to SB01_15 for minke. State this in the
  report so readers don't assume full coverage.
