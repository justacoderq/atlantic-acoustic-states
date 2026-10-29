# Vessel and weather audit

## Summary

- The three tables share one regular UTC hourly grid: 27,093 hours from
  2018-11-12 19:00 to 2021-12-15 15:00, no duplicates, no gaps.
- `combined_hourly_data.csv` equals the merge of the other two exactly.
- All 26,873 acoustic hours are on that grid. The other 220 grid hours are
  deployment gaps with no acoustic data.
- **Weather comes from two buoys** Wind, pressure, air and water
  temperature, and dew point match NDBC station **44013** (Boston). Wave height
  and periods match station **44098**. The `_44098` suffix only appears on the
  wave columns.
- `ATMP` (air temperature) and `DEWP` (dew point) have a long outage at the source (2021-07-09 onward) and cannot
  be recovered from 44013.

## Open items

- **Question for the team: air temperature and dew point.** `ATMP` and `DEWP` are
  missing from 2021-07-09 to the end of the data (about 17% of acoustic hours),
  from a sensor outage at buoy 44013 that we can't recover. Do we drop both from
  the weather summaries we compute for each acoustic state, and keep `WSPD`,
  `GST`, `PRES`, `WTMP`, and the wave fields?
  - Prachi:
  - Jacob:
  - Parker: I think we could just drop them since other columns like WTMP and wind give us similar information.
  - Decision:
- **Question for the team: wind direction.** Direction is in degrees on a circle,
  so north is both 0 and 360. A plain average of 350 and 10 gives 180 (south)
  instead of 0 (north). The hourly `WDIR` is a plain average, so about 1.1% of
  hours are wrong this way. Either (a) drop `WDIR`
  and use wind speed and gust only, or (b) replace it with `WDIR_sin` and
  `WDIR_cos`, computed from the raw readings before the hourly average (about 5
  lines in `scripts/build_full_range_csvs.py`, but it changes the shared table's
  columns). Which do we want?
  - Prachi:
  - Jacob:
  - Parker: I think we should add the WDIR_sin and WDIR_cos since they should not be too hard to add.
  - Decision:

## Weather data

- **Where it came from:** two NDBC buoys, downloaded as historical `.txt.gz` files
  (`ndbc.noaa.gov/data/historical/stdmet/<station>h<year>.txt.gz`, 2018 to 2021).
  Buoy **44013** (Boston) gives wind, gust, pressure, air and water temperature,
  and dew point. Buoy **44098** gives wave height and periods (the `_44098`
  columns).
- **How we processed it:** [`scripts/build_full_range_csvs.py`](../scripts/build_full_range_csvs.py)
  removed the missing-value placeholders (999, 99, 9999), then averaged the
  readings into one value per UTC hour.
- **Units:** wind and gust m/s, wind direction degrees true, pressure hPa,
  temperatures degrees C, wave height m, wave periods s.
- **Missing:** 2.7% of hours for wind, 1.9% for pressure and water temperature, 6.8%
  for waves, and 17% for air temperature and dew point (table below).
- **Wind direction needs care.** Direction wraps around: north is both 0 and 360,
  so averaging 350 and 10 gives 180 (south), not 0 (north). Only about 1.1% of
  hours are affected (more than 30 degrees off), but use sin/cos of WDIR or
  recompute it circularly.

| Column | Missing (acoustic hours) | Longest gap |
|---|---:|---:|
| WDIR, WSPD, GST | 2.7% | 214 h |
| PRES, WTMP | 1.9% | 142 h |
| ATMP (air temp) | 17.4% | 3,817 h |
| DEWP (dew point) | 18.2% | 3,818 h |
| WVHT, DPD, APD | 6.8% | 335 h |

Notable outages: air temperature and dew point are gone from 2021-07-09 to 2021-12-15 (a sensor
outage at 44013, not a pipeline loss). Waves are missing 2018-11-12 to 11-26 and
2021-03-09 to 03-17. All 44013 fields are missing 2019-08-19 to 08-28 and
2021-03-09 to 03-15.

## Vessel data

- **Data:** NOAA-Navy SanctSound Vessel Detection Events, Stellwagen Bank,
  [doi.org/10.25921/mas8-fj53](https://doi.org/10.25921/mas8-fj53). Our CSVs came
  from the NCEI bucket
  `gs://noaa-passive-bioacoustic/sanctsound/products/detections/sb01/` (per the
  team's `NUMBER3_vessel_env_report.md`, not re-verified).
- **Derived, not from NOAA.** NOAA supplies a list of `ship` events (18,303) with
  start and end times. `scripts/build_full_range_csvs.py` sums each event's overlap with
  each clock hour into `ship_minutes` (0 to 60). Document this as our own
  preprocessing step.
- **What it means:** detection time per hour, not vessel count, distance, or
  loudness. Mean 28.5, 15% of hours are 0, 10% are exactly 60. The 60 ceiling is
  real: no events overlap, and long events (up to 17.7 hours) fill whole hours.
- **Use `ship_minutes`, not `ship_present`.** `ship_present` is 1 in 85% of hours.
- **Missing:** 209 hours are NA. 203 are deployment gaps with no acoustic data, so
  only 6 acoustic hours lack vessel data. NA means outside the ships-metadata
  window, not "recorder off", so a few boundary hours differ from the acoustic
  coverage.
