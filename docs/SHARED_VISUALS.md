# Acoustic-only shared visuals

These outputs use only Prachi's selected acoustic K-means assignments and the
matching acoustic spectra. They do not run animal/GMM or vessel/weather/density
analyses.

## Reproduce

Run the baseline first, then generate the shared visuals:

```powershell
python -m scripts.run_acoustic_baseline
python -m scripts.run_shared_visuals
```

The visual script checks that the saved assignments match the timestamps and
deployments in the selected acoustic input. If they do not match, rerun the
baseline. Optional flags `--skip-animation` and `--skip-sonification` omit the
GIF or synthetic WAV, respectively.

## Outputs

- `results/shared/temporal/`: transition counts/probabilities, state runs and
  run-duration summaries, transitions, and state shares by month, UTC hour, and
  weekday/weekend. Only directly consecutive hours within one deployment are
  counted as transitions; runs do not cross gaps or deployment boundaries.
- `results/shared/figures/state_transition_probability.png`: conditional
  transition probabilities for adjacent observed hours.
- `results/shared/figures/state_duration_by_state.png`: observed run lengths,
  excluding runs crossing missing hours or deployment boundaries.
- `results/shared/figures/state_by_month.png` and
  `state_by_weekday_weekend.png`: descriptive state shares.
- `results/shared/figures/monthly_acoustic_fingerprint.gif`: monthly median
  acoustic spectra by state.
- `results/shared/figures/poster_research_snapshot.png`: compact poster overview
  of weekly state share, median spectra, monthly shares, and transition
  probabilities.
- `results/shared/sonification/synthetic_state_tones.wav`: daily majority
  state IDs encoded as short synthetic tones. It is not underwater audio, a
  recording, or a reconstruction.

These are exploratory visualizations of the selected baseline assignments.
State IDs are arbitrary and visual associations do not establish causes or
biological meanings.
