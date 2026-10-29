# Generative-AI use record

Generative AI assisted with extracting and organizing the supplied project
materials, auditing file names and table schemas, identifying setup gaps, and
drafting this repository scaffold and documentation.

No clustering experiments, scientific interpretations, figures, scores, or
conclusions were generated in this setup step. The team remains responsible for
and independently decides the research question, abstract representation,
methods, evaluation criteria, experimental design, interpretation, and
conclusions. Team members should add future AI assistance to this file and
identify which code, analysis, or writing it affected.

## 2026-10-29: Vessel and weather audit (Parker Suzuki)

Tool: Claude Code (Claude Sonnet 5.5).

- **What AI did:** read the project docs and the assignment, ran scripts to check
  the hourly vessel and weather tables (missing values, time grid, how they were
  built), re-downloaded the NDBC buoy files to confirm where the weather columns
  came from, drafted `docs/VESSEL_WEATHER_AUDIT.md`, and changed only the file
  paths in `scripts/build_full_range_csvs.py` so it runs from this repo.
- **What I did:** reviewed the audit and the results, decided what to cut and what
  to keep, chose which open questions to put to the team, and made the edits. The
  open questions (air temperature and dew point, wind direction) are for the team
  to decide, not AI.
- **What it affected:** `docs/VESSEL_WEATHER_AUDIT.md` (writing and analysis) and
  `scripts/build_full_range_csvs.py` (file paths only, no change to the logic;
  output checked identical to the existing tables). No clustering, figures, or
  scientific conclusions were produced.
