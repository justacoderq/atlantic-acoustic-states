# Research questions

## Central question

Can unsupervised data-mining methods discover recurring acoustic states in
Stellwagen Bank, and how are those states related to time, vessel activity,
weather, and animal presence?

## Supporting questions

1. **Recurring structure:** Do multiple unsupervised methods recover useful
   groups or continuous structure from standardized acoustic spectra? How
   sensitive are the results to representation, parameters, and random seeds?
2. **Temporal rhythms:** How do acoustic states vary by hour of day, weekday
   versus weekend, month, and season?
3. **State dynamics:** What are the observed state run lengths and transition
   patterns when gaps and deployment boundaries are respected?
4. **External interpretation:** How do vessel activity, weather/ocean
   measurements, and animal detections vary across acoustically discovered
   states, when compared at their native time resolutions?
5. **Unusual periods:** Do density-clustering noise points or other unusual
   acoustic observations align with notable vessel, weather, animal, or data
   conditions?

## Representation and evaluation guardrails

- Fit baseline clusters using acoustic bands only; standardize those bands.
- Keep time and deployment identifiers out of the numerical acoustic feature
  matrix. Use them to order observations and prevent invalid cross-gap or
  cross-deployment transitions.
- Treat vessel, weather, and animal variables as external interpretation or
  validation data initially; do not train a classifier to predict those labels.
- Keep daily, hourly, and detection-interval animal observations at their
  recorded resolutions.
- Compare multiple methods using internal quality, cluster sizes, stability,
  interpretability, and temporal coherence—not a single score alone.
- Give discovered groups neutral state identifiers until measured profiles and
  independent interpretation support descriptive names.

## Decisions for the team to make together

- What definition of “recurring acoustic state” is meaningful for this data?
- Which clustering results are stable and interpretable enough to analyze
  temporally?
- How should missing hours, deployment boundaries, and incomplete external
  observations be handled in each comparison?
- Which state labels, if any, are justified by the measured acoustic and
  external-variable profiles?
- Which experiments are essential for the final report, and which are
  exploratory?
