# Prachi's acoustic preprocessing and baseline

## Reproduce

From the repository root:

```powershell
python -m pip install -r requirements.txt
python -m scripts.run_acoustic_baseline
```

The default input is `Data Mining Project/all.csv`. The script accepts
`--input`, `--processed-dir`, `--results-dir`, and
`--silhouette-sample-size` overrides.

Run the focused tests with:

```powershell
python -m pytest -q tests/test_acoustic_baseline.py
```

## Representation and preprocessing

The loader pivots the long acoustic table into one row per timestamp and one
column per frequency band, sorted by timestamp. It checks that time, frequency,
deployment, and sound pressure are valid; each timestamp belongs to one
deployment; every `(time, frequency)` key is unique; and no hourly spectrum has
missing bands. It fails loudly rather than imputing data.

The numeric feature matrix contains the 33 acoustic bands only. Timestamp and
deployment are stored in the separate, row-aligned
`data/processed/acoustic_observations.csv` metadata file. Each acoustic
frequency band is standardized with `StandardScaler`; PCA and K-means do not
receive metadata, vessel data, weather data, or animal observations.

The PCA model is fitted to the full standardized 33-dimensional acoustic
matrix. The baseline uses the smallest number of leading components reaching
at least 90% cumulative explained variance.

An additional acoustic-only summary matrix is generated for later feature
comparisons, but it is not used to fit this K-means baseline. Its low-, mid-,
and high-band means are arithmetic means of stored levels with band-center
boundaries <=250 Hz, >250 to <=2000 Hz, and >2000 Hz. Broadband mean is the
arithmetic mean over all 33 bands. Spectral slope is the least-squares slope of
level against log10 frequency. Normalized spectral entropy uses
`p_i = 10^(L_i/10) / sum_j 10^(L_j/10)` and divides Shannon entropy by
`log(33)`; interpreting this as a power-based entropy assumes the stored levels
are dB. Verify the product units before assigning scientific meaning.

## K-means evaluation

The baseline evaluates `k = 2` through `k = 8`, with random seeds 42, 123, and
2026 and `n_init=10` per fit. It records inertia, sampled silhouette, Davies–
Bouldin score, iterations, and cluster sizes for every seed and `k`. Silhouette
uses the same fixed 3,000-observation sample (or all observations if fewer);
the other two internal metrics use the full projected matrix. Pairwise
Adjusted Rand Index (ARI) across seeds at each `k` summarizes initialization
stability.

For the state timeline and profiles, `k` is selected as the tested value with
the largest mean sampled silhouette. The stored assignment uses the lowest
inertia run among the three seeds at that selected `k`. This rule is a
reproducible baseline decision, not evidence that the chosen number of states
is uniquely correct or scientifically optimal. State identifiers are
arbitrary; do not assign acoustic names without independent interpretation.

## Generated outputs

Processed features:

- `data/processed/acoustic_feature_matrix_standardized.csv`
- `data/processed/acoustic_interpretable_features.csv`
- `data/processed/acoustic_observations.csv`

Tables:

- `results/logs/acoustic_baseline_summary.md`: generated human-readable metrics
  and assignment sizes for the run.
- `results/tables/baseline_run_metadata.csv`: input dimensions, retained PCA
  components, selection rule and selected run.
- `results/tables/pca_explained_variance.csv`: variance ratio by component.
- `results/tables/kmeans_runs.csv`: all seed-by-`k` metrics.
- `results/tables/kmeans_summary.csv`: mean and standard deviation by `k`,
  including pairwise seed stability.
- `results/tables/kmeans_cluster_sizes.csv`: sizes for each state in each
  seed-by-`k` solution.
- `results/tables/kmeans_seed_stability.csv`: pairwise ARI values.
- `results/tables/kmeans_median_profiles.csv` and
  `kmeans_median_profiles_long.csv`: median unstandardized acoustic profile by
  selected state.
- `results/tables/kmeans_state_by_hour.csv`: state counts and fractions by
  UTC hour-of-day.

Assignment and figures:

- `results/cluster_assignments/kmeans_selected_assignments.csv`
- `results/figures/pca_explained_variance.png`
- `results/figures/kmeans_selection.png`
- `results/figures/kmeans_acoustic_profiles.png`
- `results/figures/kmeans_state_timeline.png`
- `results/figures/kmeans_state_by_hour.png`

The timeline is drawn as individual points, not connected lines, to avoid
visually implying continuity across gaps. Deployment boundaries and larger
gaps still require explicit handling in later transition analyses.

## Interpretation cautions

- PCA is fit once on the observed dataset, so this is a descriptive baseline,
  not a held-out predictive evaluation.
- Standardization gives each band unit variance; it changes the relative
  influence of bands compared with raw sound-level distances.
- The silhouette estimate is based on a fixed sample, so it is an estimate,
  not a full pairwise evaluation over all hourly observations.
- K-means prefers compact Euclidean groups and may not represent transitional,
  elongated, or density-shaped acoustic structure.
- Do not infer that a state is “quiet,” vessel-dominated, weather-driven, or
  biologically active from its ID. Use the profile and independent external
  variables to assess interpretations.
- Because deployment and time are excluded from fitting, inspect state
  profiles for deployment artifacts before making scientific claims.
