# Mining the Daily Rhythms of the Atlantic Ocean

Data-mining project for CS 6/5140 / DS 4140, Fall 2026, with instructor
Jeff M. Phillips at the University of Utah.

**Team:** Prachi Aswani, Jacob Erard, Parker Suzuki

**Intermediate report:** November 3, 2026, at 10:00 a.m.

## Research question

Can an explicit similarity measure between complete daily acoustic time-series
objects discover recurring ocean-sound motifs and unusual days at Stellwagen
Bank?  Once those acoustic structures are discovered, what external evidence
is consistent with vessel, weather, or animal explanations?

The central representation is a complete `24 x 33` UTC-day sound-level matrix.
We compare level-sensitive and shape-only acoustic distances, then mine
nearest-neighbor motifs, mutual-kNN neighborhoods, and isolated days. Vessel,
weather, animal, calendar, and existing state variables are reserved for later
interpretation; they are not inputs to the acoustic distance.

See [docs/RESEARCH_QUESTIONS.md](docs/RESEARCH_QUESTIONS.md) for the agreed
question set and [docs/TEAM_CONTRIBUTIONS.md](docs/TEAM_CONTRIBUTIONS.md) for
the proposed three-person work split.

## Current repository state

The supplied archive is extracted and its original contents are preserved in
`Data Mining Project/`. Prachi's acoustic-only baseline and its reproducible
results are implemented. Parker's vessel/weather source audit and hourly table
builder are also integrated. Jacob's animal-data audit, derived alignment
tables, and exploratory GMM results are now integrated; density clustering is
still pending. See [data/README.md](data/README.md) for the dataset
inventory and known audit limitations, [docs/VESSEL_WEATHER_AUDIT.md](docs/VESSEL_WEATHER_AUDIT.md)
for the vessel/weather audit, and [DATA_SOURCES.md](DATA_SOURCES.md) for source
  references and provenance gaps. See [docs/ANIMAL_AUDIT.md](docs/ANIMAL_AUDIT.md)
  for the animal-data validation and comparison constraints.

The original notebooks and source data remain in their extracted locations to
avoid breaking paths or keeping duplicate copies. New shared scripts, notebooks,
tests, processed files, and results should use the folders scaffolded in this
repository.

## Suggested local setup

From the repository root in PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The original notebooks are preserved under `Data Mining Project/`. Their
existing relative paths may assume a different working directory; check paths
before running or updating them.

## Collaboration

Create personal feature branches when the team is ready; this setup has not
created any branches or commits. Suggested starting names and ownership areas
are in [docs/TEAM_CONTRIBUTIONS.md](docs/TEAM_CONTRIBUTIONS.md). Share changes
through pull requests and review data-processing decisions together.

## Prachi's acoustic baseline

The reproducible acoustic-only preprocessing and PCA/K-means baseline is in
`src/` and `scripts/run_acoustic_baseline.py`. From the repository root, install
dependencies with `python -m pip install -r requirements.txt`, then run:

```powershell
python -m scripts.run_acoustic_baseline
```

The script writes the standardized acoustic matrix and aligned metadata under
`data/processed/`, and actual metrics, state assignments, and figures under
`results/`. See [docs/PRACHI_ACOUSTIC_BASELINE.md](docs/PRACHI_ACOUSTIC_BASELINE.md)
for method details, output descriptions, and interpretation cautions.

## Shared acoustic visuals

After running the acoustic baseline, generate temporal summaries and
acoustic-only presentation media with:

```powershell
python -m scripts.run_shared_visuals
```

This generates deployment/gap-aware state dynamics, a poster snapshot, a
monthly acoustic-fingerprint GIF, and synthetic state-tone audio under
`results/shared/`. The audio encodes state IDs as tones; it is not underwater
recording or reconstructed audio. See
[docs/SHARED_VISUALS.md](docs/SHARED_VISUALS.md) for output descriptions.

## Ocean-rhythm discovery

Run the periodicity, repeated-motif, change-point, anomaly, post-hoc context,
interactive timeline, animation, and synthetic-sonification pipeline with:

```powershell
python -m scripts.run_ocean_rhythm
```

See [docs/OCEAN_RHYTHM.md](docs/OCEAN_RHYTHM.md). The presentation assets use
processed sound-level data; synthetic tones are not original underwater audio.

## Distance-first daily motif mining

The project’s central data-mining analysis represents one complete UTC day as
a `24 x 33` acoustic time-series object. It compares a level-sensitive distance
against a shape-only distance, then mines nearest-neighbor motifs, a mutual-kNN
similarity graph, and isolated days. Run it with:

```powershell
python -m scripts.run_distance_first_analysis
```

See [docs/DISTANCE_FIRST_PROJECT.md](docs/DISTANCE_FIRST_PROJECT.md). PCA,
K-means, and GMM remain baselines; vessel, weather, and animal observations
are used only after acoustic patterns are found.

## AI-use record

AI assistance used for repository setup and data-inventory documentation is
recorded in [docs/AI_USAGE.md](docs/AI_USAGE.md). The team should update it as
work continues.
