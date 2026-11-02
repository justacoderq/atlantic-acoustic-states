# Data inventory

The supplied archive was extracted without changing its original contents.
Source files remain under `Data Mining Project/` to preserve existing notebook
paths and avoid duplicate copies. Reproducible processed data produced by the acoustic baseline lives under
`processed/`. Do not copy duplicate source datasets here.

## Verified files

| File (under `Data Mining Project/`) | Size (bytes) | Observed structure |
|---|---:|---|
| `all.csv` | 70,211,050 | 886,809 rows × 5 columns: source file, deployment, UTC time, frequency, sound pressure level. 33 frequencies (13–20,000 Hz), 26,873 unique hourly timestamps, 18 deployments. No missing cells or exact duplicate rows. |
| `combined_hourly_data.csv` | 11,991,581 | 27,093 hourly rows. Contains 33 acoustic-band columns, deployment, two vessel measurements, and ten weather/ocean measurements, plus an exported `Unnamed: 0` time-index column (47 columns total). 220 missing acoustic rows; the remaining missing counts are in source variables below. Treat as a derived candidate, not an authoritative source, until the merge is revalidated. |
| `ships_hourly.csv` | 1,210,850 | 27,093 hourly rows; UTC time, deployment, ship minutes, ship presence. 209 missing values in each of the three data columns; no exact duplicate rows. |
| `weather_hourly.csv` | 2,796,785 | 27,093 hourly rows; ten weather/ocean variables. Missing counts: WDIR/WSPD/GST 734 each; PRES 522; ATMP 4,684; WTMP 523; DEWP 4,908; WVHT_44098/DPD_44098/APD_44098 1,937 each. No exact duplicate rows. |
| `Animal sounds/animals.csv` | 13,844,443 | 154,798 rows × 6 columns; no missing cells or exact duplicate rows. Contains 8 animal categories, 18 deployments, and nominal daily/hourly/detection-interval values. The CSV requires validation against the raw NetCDF products before it is used for animal/state comparisons; that analysis is not implemented in this branch. |
| `all.xlsx` | 22,346,195 | One worksheet with the same five column names as `all.csv`. It appears to be another representation of the acoustic table; full content equality has not been verified. Avoid using or committing both copies unless needed. |
| `Animal sounds/raw/*.nc` | 105 files | Deployment/species NetCDF products. Files are HDF5-based; the currently available SciPy NetCDF-3 reader could not read them. The animal-data audit and comparison work remains with its owner and is not included in this branch. |

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
- The prior combined animal CSV has not been validated for animal/state
  comparisons in this branch. Jacob's work should compare it against the raw
  NetCDF products before analysis.
- `team_dataset_summary.csv` is a prior summary, not a source of truth. Audit
  outputs should be regenerated from raw files and checked before reporting.

The archive contained 117 files totaling approximately 127.6 MB uncompressed.
No individual archived file exceeded 100 MB. The largest extracted file is
`all.csv` at 70,211,050 bytes. The original ZIP is retained at the repository
root; avoid committing both the ZIP and its extracted duplicate data unless
there is a deliberate reason.

## Generated acoustic preprocessing output

Running `python -m scripts.run_acoustic_baseline` writes:

- `processed/acoustic_feature_matrix_standardized.csv`: numeric-only,
  timestamp-sorted z-scored spectrum; the columns are the acoustic feature
  matrix and contain no timestamps or deployment identifiers.
- `processed/acoustic_interpretable_features.csv`: numeric-only derived
  summaries. Band means use centers <=250 Hz (low), >250 to <=2000 Hz (mid),
  and >2000 Hz (high); the broadband mean is over all bands, the spectral slope
  is the least-squares slope against log10 frequency, and normalized spectral
  entropy uses relative weights 10^(level/10), assuming stored levels are dB.
- `processed/acoustic_observations.csv`: row index, UTC timestamp, and
  deployment metadata aligned row-for-row with that matrix.

These outputs are generated from the preserved long-format `all.csv`; the
matrix does not silently fill missing hours or impute incomplete spectra.

Acoustic-only temporal and presentation visuals are generated under
`results/shared/` by `python -m scripts.run_shared_visuals`. The animal/GMM and
vessel/weather/density analyses are not part of this branch.
