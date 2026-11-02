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

## 2026-10-31: Animal data audit (Jacob Erard)

Tool: Claude Code (Claude Opus 5.5).

- **What AI did:** read the 105 animal NetCDF files and their metadata, wrote
  `scripts/audit_animals.py` to compare them against `Animal sounds/animals.csv`,
  generated the tables in `results/tables/animal_*.csv`, and drafted
  `docs/ANIMAL_AUDIT.md`.
- **What I did:** _(to fill in: what you reviewed, changed, and decided)_
- **What it affected:** `scripts/audit_animals.py`, `docs/ANIMAL_AUDIT.md`, and
  the three `results/tables/animal_*.csv` outputs. No clustering, figures, or
  scientific conclusions were produced. The open questions in the audit are for
  the team to decide.
