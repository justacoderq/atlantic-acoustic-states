# Mining the Daily Rhythms of the Atlantic Ocean

Data-mining project for CS 6/5140 / DS 4140, Fall 2026, with instructor
Jeff M. Phillips at the University of Utah.

**Team:** Prachi Aswani, Jacob Erard, Parker [last name to be added]

**Intermediate report:** November 3, 2026, at 10:00 a.m.

## Research question

Can unsupervised data-mining methods discover recurring acoustic states in
Stellwagen Bank, and how are those states related to time, vessel activity,
weather, and animal presence?

The project treats the observations as a multiview time series. The initial
clustering space is the standardized 33-band acoustic spectrum. Vessel,
weather, animal, and calendar variables are reserved for later interpretation
and validation; they are not labels for a central classifier.

See [docs/RESEARCH_QUESTIONS.md](docs/RESEARCH_QUESTIONS.md) for the agreed
question set and [docs/TEAM_CONTRIBUTIONS.md](docs/TEAM_CONTRIBUTIONS.md) for
the proposed three-person work split.

## Current repository state

The supplied archive is extracted and its original contents are preserved in
`Data Mining Project/`. No experiments or results have been generated as part
of this setup. See [data/README.md](data/README.md) for a verified inventory
and known audit limitations, and [DATA_SOURCES.md](DATA_SOURCES.md) for source
references and provenance gaps.

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

## AI-use record

AI assistance used for repository setup and data-inventory documentation is
recorded in [docs/AI_USAGE.md](docs/AI_USAGE.md). The team should update it as
work continues.
