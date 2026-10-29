# Team contributions and working plan

The ownership below is a starting point for the three-person team. Agree on
shared definitions and evaluation criteria together before interpreting
results. The Parker surname is still to be added.

| Team member | Primary ownership | Initial tasks and expected handoff |
|---|---|---|
| **Prachi Aswani** | Repository integration, acoustic preprocessing, feature engineering, PCA, K-means baseline, shared comparison notebook, report integration | Confirm the acoustic long-to-wide representation and missing-hour policy; document acoustic-only preprocessing; build and validate the first reproducible baseline; share the feature/assignment schema with the team. Suggested branch: `prachi/acoustic-baseline`. |
| **Jacob Erard** | Animal-data audit, species and temporal-resolution documentation, GMM experiments, daily animal/state alignment, biological interpretation | Verify NetCDF metadata against `animals.csv`; identify coverage and native resolutions per product; compare GMM results on the shared acoustic representation; align daily animal observations to daily state summaries without hourly replication. Suggested branch: `jacob/animal-gmm`. |
| **Parker Suzuki** | Vessel/weather audit, exact source and unit documentation, HDBSCAN or DBSCAN experiments, vessel/weather interpretation, unusual-event analysis | Verify vessel and weather provenance, units, missingness, and overlap; test density clustering on the agreed acoustic representation; summarize external weather/vessel profiles and investigate candidate unusual periods without assuming their cause. Suggested branch: `parker/density-context`. |

## Shared responsibilities

- Finalize the research question, abstract representation, and evaluation
  criteria.
- Agree on timestamp, deployment-gap, missing-data, and animal-resolution
  handling before comparing results.
- Review each other's pull requests and reproduce each other's key outputs.
- Interpret results and decide which conclusions are supported by evidence.
- Prepare the intermediate report, final report, poster, and presentation.
- Update this table and the AI-use record if responsibilities change.

## Suggested collaboration sequence

1. Each person creates their own feature branch from the team's agreed base;
   this setup did not create branches or commits.
2. Agree on input/output schemas and shared terminology before separate method
   work begins.
3. Keep method-specific work isolated on each branch and open pull requests
   with concise reproduction steps.
4. Merge only after another team member reviews the data treatment and can
   reproduce the result.
5. Record shared decisions and unresolved limitations in the project docs.
