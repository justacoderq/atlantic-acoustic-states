# Email to Jeff: distance-first revision

**Subject:** Revised distance-first plan for *The Secret Rhythm of the Ocean*

Hi Jeff,

Thank you for the feedback. We realized that our earlier presentation made
PCA/K-means look like the project, rather than clearly defining the object,
representation, distance, and structure we are mining. We have rebuilt the
project around that distinction.

Our primary object is now one complete, contiguous UTC day of acoustic data: a
24 by 33 time-frequency matrix. We exclude partial days, recording gaps, and
deployment boundaries. We compare daily objects using two explicit RMS
Euclidean distances:

1. A **level-sensitive** distance: standardized hourly frequency-band levels.
   It treats two days as different when their loudness or their daily evolution
   differs.
2. A **shape-only** distance: remove each hour's broadband mean before the same
   standardization and distance. It asks whether the spectral shape evolves
   similarly even if one day is louder.

We have 1,101 valid daily objects. From these distances we now mine: (1)
nearest non-overlapping daily motifs, (2) a mutual 10-nearest-neighbor graph
of similar days, and (3) isolated days using their mean distance to nearest
neighbors. The two representations make the same top nearest-neighbor choice
only 21.3% of the time, so the representation choice materially changes what
we call similar. For example, the closest shape-only motif is Nov. 27, 2021
and Nov. 29, 2019; our next step is to inspect those concrete examples and
then use ship, weather, and animal data only as held-out context for an
interpretation.

PCA/K-means/GMM are now only baselines. We are not using ship, weather,
animals, calendar labels, or existing state labels to construct the acoustic
distance.

Could you please tell us whether this is now the right direction?

1. Is the complete 24-hour matrix the right primary object, or should a
   7-day object be primary instead?
2. Is comparing these two deliberately different distances a meaningful
   modeling comparison before adding an optional time-series foundation-model
   embedding?
3. Does nearest-neighbor motifs + mutual-kNN structure + distance-based
   outliers match the kind of structure you want us to discover?

We have included a concise technical packet with the formulas, result tables,
and motif figures in `results/distance_first/JEFF_FEEDBACK_PACKET.md`.

Thank you,

Prachi, Jacob, and Parker
