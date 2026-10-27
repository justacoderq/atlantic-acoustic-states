# Data inventory

The supplied archive was extracted without changing its original contents.
Source files remain under `Data Mining Project/` to preserve existing notebook
paths and avoid duplicate copies. This directory is reserved for future
reproducible processed data and small samples; do not copy source datasets here
without a team decision.

## Verified files

| File (under `Data Mining Project/`) | Size (bytes) | Observed structure |
|---|---:|---|
| `all.csv` | 70,211,050 | 886,809 rows × 5 columns: source file, deployment, UTC time, frequency, sound pressure level. 33 frequencies (13–20,000 Hz), 26,873 unique hourly timestamps, 18 deployments. No missing cells or exact duplicate rows. |
| `combined_hourly_data.csv` | 11,991,581 | 27,093 hourly rows. Contains 33 acoustic-band columns, deployment, two vessel measurements, and ten weather/ocean measurements, plus an exported `Unnamed: 0` time-index column (47 columns total). 220 missing acoustic rows; the remaining missing counts are in source variables below. Treat as a derived candidate, not an authoritative source, until the merge is revalidated. |
| `ships_hourly.csv` | 1,210,850 | 27,093 hourly rows; UTC time, deployment, ship minutes, ship presence. 209 missing values in each of the three data columns; no exact duplicate rows. |
| `weather_hourly.csv` | 2,796,785 | 27,093 hourly rows; ten weather/ocean variables. Missing counts: WDIR/WSPD/GST 734 each; PRES 522; ATMP 4,684; WTMP 523; DEWP 4,908; WVHT_44098/DPD_44098/APD_44098 1,937 each. No exact duplicate rows. |
| `Animal sounds/animals.csv` | 13,844,443 | 154,798 rows × 6 columns; no missing cells or exact duplicate rows. Contains 8 animal categories, 18 deployments, and `daily` (109,850 rows), `hourly` (26,842), and `detection_interval` (18,106) source resolutions. No duplicate `(time, deployment, animal)` keys. |
| `all.xlsx` | 22,346,195 | One worksheet with the same five column names as `all.csv`. It appears to be another representation of the acoustic table; full content equality has not been verified. Avoid using or committing both copies unless needed. |
| `Animal sounds/raw/*.nc` | 105 files | Deployment/species NetCDF products. Files are HDF5-based; the currently available SciPy NetCDF-3 reader could not read them. Inspect later with an installed NetCDF4-compatible reader and compare metadata against the combined animal CSV. |

The main acoustic, vessel, and weather tables span 2018-11-12 19:00 UTC
through 2021-12-15 15:00 UTC. The acoustic table has 26,873 unique hours over
that period. The hourly vessel and weather tables each cover a regular
27,093-hour calendar sequence. Missing acoustic hours must remain missing;
they should not be filled with invented values for clustering.

## Preserved project materials and audit notes

- `Data Mining Project/Data Inspection.ipynb` and `DM Sound.ipynb` are original
  notebooks; their source contains no URL literals.
- `Data Mining Project/Data Collection Report.docx` is preserved as supplied.
- `Animal sounds/animal_column_summary.csv` is a prior summary and should be
  regenerated from source when needed.
- `Animal sounds/animal_raw_file_summary.csv` is empty (1 byte); it is not
  usable as an inventory.
- `team_dataset_summary.csv` is a prior summary, not a source of truth. Audit
  outputs should be regenerated from raw files and checked before reporting.

The archive contained 117 files totaling approximately 127.6 MB uncompressed.
No individual archived file exceeded 100 MB. The largest extracted file is
`all.csv` at 70,211,050 bytes. The original ZIP is retained at the repository
root; avoid committing both the ZIP and its extracted duplicate data unless
there is a deliberate reason.

For animal comparisons, keep the supplied temporal resolution. Compare daily
presence against daily summaries of acoustic-state assignments; do not repeat
one daily label across 24 hourly rows.
