# Distance-first feedback packet for Jeff

## The pivot

We now treat one complete UTC day as one acoustic time-series object: a 24 x 33 matrix of observed sound levels. We mine structure by comparing these objects with explicit distances, rather than making PCA/K-means the central result.

## Representations and distances

1. **Level-sensitive representation:** each day is a 24 x 33 matrix; every frequency band is standardized over all observed hours, then the flattened daily matrices are compared with root-mean-square Euclidean distance. This preserves overall level and within-day evolution.
2. **Shape-only representation:** each hour has its broadband mean subtracted before the same standardization and RMS Euclidean distance. This removes hour-to-hour overall loudness so it compares spectral shape instead.

For flattened daily vectors `u` and `v` with `d = 24 x 33` entries, both reported distances use `sqrt(sum((u - v)^2) / d)`. The representation supplied to that formula is the deliberate modeling choice.

There are **1,101 complete, contiguous daily objects**. Candidate motif neighbors must be at least 14 calendar days apart, preventing a day from matching the day immediately before or after it.

## What we mine from the distance

- nearest non-overlapping neighbors: repeated daily motifs;
- a mutual 10-nearest-neighbor graph: neighborhoods of days that select each other as similar;
- mean distance to ten nearest historical days: isolated, acoustically unusual days.

## Early concrete results

The rank-one nearest-neighbor agreement between the level-sensitive and shape-only representations is **21.3%**. This disagreement is useful: it identifies days that are similar in loudness but not spectral shape, or vice versa.

### Closest level-sensitive motifs

| motif_rank | source_date | neighbor_date | distance |
| --- | --- | --- | --- |
| 1 | 2021-12-13 00:00:00+00:00 | 2021-01-04 00:00:00+00:00 | 0.3096620899335266 |
| 2 | 2020-03-30 00:00:00+00:00 | 2020-11-24 00:00:00+00:00 | 0.3553411737996902 |
| 3 | 2021-11-27 00:00:00+00:00 | 2019-11-29 00:00:00+00:00 | 0.36036313667210135 |

### Closest shape-only motifs

| motif_rank | source_date | neighbor_date | distance |
| --- | --- | --- | --- |
| 1 | 2021-11-27 00:00:00+00:00 | 2019-11-29 00:00:00+00:00 | 0.28306510935821905 |
| 2 | 2021-01-04 00:00:00+00:00 | 2021-12-03 00:00:00+00:00 | 0.31552163650872755 |
| 3 | 2020-12-18 00:00:00+00:00 | 2021-01-05 00:00:00+00:00 | 0.37180227188523524 |

### Most isolated daily objects under shape-only distance

| outlier_rank | date | deployment | mean_knn_distance |
| --- | --- | --- | --- |
| 1 | 2020-10-02 00:00:00+00:00 | SB01_12 | 1.5434362901697694 |
| 2 | 2021-07-09 00:00:00+00:00 | SB01_16 | 1.4354706866207845 |
| 3 | 2021-07-12 00:00:00+00:00 | SB01_16 | 1.353293945283713 |
| 4 | 2021-07-11 00:00:00+00:00 | SB01_16 | 1.3107838336609419 |
| 5 | 2019-02-04 00:00:00+00:00 | SB01_02 | 1.2999478927528973 |

## Questions for feedback

1. Is a complete 24-hour acoustic matrix the right primary object, or should we also make a seven-day object the main unit?
2. Is this two-distance comparison a sufficiently meaningful modeling comparison, before we add an optional time-series foundation-model embedding?
3. Is the mutual-kNN graph plus nearest-neighbor motifs and outlier ranking the right notion of structure for this project?

PCA/K-means and GMM remain baselines. Vessel, weather, and animal variables are held out of distance construction and used only after discovery to interpret selected motifs or unusual days.
