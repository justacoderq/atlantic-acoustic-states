# Implementation log: distance-first revision for Jeff feedback

## Purpose

This log records the changes made after Jeff's feedback that the project needs
an explicit representation and distance between data objects, followed by a
clear story about structure found from that distance.

## Completed

1. **Reframed the central question.** The main question is now whether an
   acoustic distance between complete daily time-series objects reveals
   recurring motifs and unusual days. PCA/K-means/GMM are baselines rather than
   the main contribution.
2. **Defined valid daily objects.** `src/daily_similarity.py` builds one
   `24 x 33` UTC-day matrix only when all 24 hours are contiguous and belong to
   one deployment. It excludes partial days, gaps, and deployment crossings.
   The raw `all.csv` table has one long row per timestamp-frequency measurement;
   validation and pivoting turn its 886,809 rows into 26,873 hourly,
   33-dimensional acoustic vectors before daily matrices are formed.
3. **Implemented and documented two distances.** The level-sensitive and
   shape-only representations use RMS Euclidean distance after bandwise
   standardization. Shape-only data removes each hour's broadband mean before
   standardization.
4. **Mined structure from the distance.** The analysis produces non-overlapping
   nearest-neighbor motifs, a mutual 10-nearest-neighbor graph, and an outlier
   ranking from mean 10-neighbor distance.
5. **Kept interpretation separate from discovery.** Vessel, weather, animal,
   calendar, and prior state variables are not distance inputs. They are merged
   after acoustic motifs or outliers are selected.
6. **Ran the real analysis.** The current data yield 1,101 complete daily
   objects. The two representations agree on the rank-one neighbor for 21.3%
   of days. Outputs are in `results/distance_first/`.
7. **Tested the implementation.** A new unit test confirms partial days are
   excluded and that adding a uniform loudness offset leaves shape-only
   distance near zero. The full repository test suite passed: 10 tests passed
   (one environment-only joblib core-count warning).
8. **Prepared feedback artifacts.**
   - `docs/JEFF_FEEDBACK_EMAIL.md`: concise email text.
   - `results/distance_first/JEFF_FEEDBACK_PACKET.md`: technical packet with
     real result tables.
   - `docs/JEFF_DISTANCE_FIRST_ONE_PAGER.tex`: one-page LaTeX summary and
     feedback request.
9. **Tried local LaTeX compilation.** The installed TinyTeX `pdflatex` and
   `xelatex` executables fail before reading the source with the local Windows
   error `Can't get long name for C:\\Users\\Prachi\\AppData.` The LaTeX source
   has therefore been prepared and checked as text, but PDF generation needs a
   working local TeX installation (or Overleaf) before sending a PDF.

## Deliberately not claimed or implemented yet

- We do not claim that ships, weather, or animals caused any motif or outlier.
- We do not claim the discovered groups are physical ocean ``states.''
- A pre-trained time-series foundation-model embedding is not yet included.
  It is an optional third representation that needs Jeff's confirmation and a
  model-selection decision; the transparent distance baseline is complete now.
- We have not chosen whether a 24-hour or 7-day object should be primary. That
  is a focused question for Jeff.

## Requested next feedback

1. Confirm or revise the daily-object choice.
2. Confirm or revise the two-distance comparison.
3. Confirm whether nearest neighbors, mutual-kNN neighborhoods, and isolation
   are the desired structure-mining tools before we extend the study.

## Provenance and responsibility

The generative-AI disclosure for this work is recorded in `docs/AI_USAGE.md`.
The team remains responsible for reviewing the method, selecting the final
claims, checking selected cases, and interpreting external context.
