# The Secret Rhythm of the Ocean

Run the complete analysis from the repository root:

```powershell
python -m scripts.run_ocean_rhythm
```

The pipeline discovers structure only from the hourly acoustic spectrum and
joins ships, weather, animal detections, and baseline states only after the
fact for interpretation. It does not make causal claims from those joins.

## Outputs

- `periodicity_autocorrelation.csv` and figure: daily/weekly/longer-lag
  feature autocorrelations, calculated within contiguous deployment segments.
- `motifs.csv` and figure: repeated seven-day, multifeature acoustic patterns.
  This is a transparent sampled matrix-profile approximation; it does not
  bridge missing days or deployments.
- `change_points.csv`: well-spaced abrupt daily shifts scored from the acoustic
  feature change across two seven-day windows.
- `daily_rhythm.csv`: acoustic-only isolation-forest outlier score and a
  combined unusualness score. These identify candidates for investigation,
  not confirmed storms, ships, or animal events.
- `daily_context.csv`, `state_external_context.csv`, and
  `animal_state_context.csv`: post-hoc summaries for evidence-based
  interpretation.
- `gap_aware_state_transitions.csv`: baseline-state transitions that exclude
  deployment boundaries and gaps.

## Presentation assets

`results/ocean_rhythm/interactive/index.html` is an offline click-to-inspect
timeline. The figures folder contains calendar, motif, change-point, and
external-context visuals plus an animated calendar. The media folder contains
a state-dynamics GIF and a synthetic sonification of unusualness. The latter
is explicitly a tone encoding, not raw underwater audio or a reconstruction.

## Short narrated-video outline

1. Show the calendar animation: “Does the ocean have a daily heartbeat?”
2. Reveal the autocorrelation peaks and repeated motifs.
3. Click a top unusual day in the timeline, then show ship/weather/animal
   context as possible explanations.
4. Close on the state-dynamics animation: different tools reveal periodic,
   repeated, abrupt, and unusual aspects of the same soundscape.
