# Distance-first project pivot

## New central question

Can an explicit similarity measure between complete daily acoustic time-series
objects reveal recurring ocean-sound motifs and unusual days at Stellwagen
Bank?

This replaces “run K-means on hourly spectra” as the central project story.
PCA, K-means, and GMM are retained as baselines, not as the main discovery.

## Object, representation, and distance

One object is one complete UTC day from one deployment: a `24 x 33` matrix of
sound levels. Partial days, deployment boundaries, and hours separated by gaps
are excluded.

We compare two representations:

1. **Level-sensitive:** standardize each frequency band over all observed
   hours, flatten the `24 x 33` daily object, and use root-mean-square L2
   distance. This captures level and daily evolution.
2. **Shape-only:** subtract each hour's broadband mean before standardizing
   and applying the same distance. This makes a loud and a quiet version of
   the same spectral shape close together.

For daily vectors `u` and `v` with `d = 24 x 33` entries, the reported
distance is `sqrt(sum((u - v)^2) / d)`. The only difference between the two
distances is the representation supplied to this formula, which lets us test
whether absolute level changes the discovered structure.

Neither representation contains ship, weather, animal, calendar, or existing
cluster-state variables. Those are joined only after patterns are mined.

## Structure mined from the distance

- Closest non-overlapping nearest neighbors are recurring daily motifs.
- A mutual 10-nearest-neighbor graph exposes neighborhoods of days that select
  each other as similar.
- Mean distance to ten non-overlapping nearest neighbors ranks isolated,
  acoustically unusual days.

The two distances are deliberately compared. A useful result is not merely a
cluster color: it is an example where level-sensitive and shape-only similarity
make different, explainable decisions.

## Three-person responsibilities

| Person | Ownership |
|---|---|
| Prachi | Daily-window construction; level-sensitive versus shape-only distance; nearest-neighbor motif examples and distance comparison. |
| Jacob | Correct native-resolution animal interpretation for selected motifs/outliers; comparison of transparent distances with GMM or an optional time-series embedding. |
| Parker | Mutual-kNN graph and isolation analysis; vessel/weather context for selected motifs/outliers; missing-data and confounding checks. |

## Run

```powershell
python -m scripts.run_distance_first_analysis
```

The generated `results/distance_first/JEFF_FEEDBACK_PACKET.md` is the concise
artifact to send before the next feedback meeting.
