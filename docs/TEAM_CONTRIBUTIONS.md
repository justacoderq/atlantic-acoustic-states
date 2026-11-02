# Team contributions and working plan

The ownership below is a starting point for the three-person team. Agree on
shared definitions and evaluation criteria together before interpreting
results. The Parker surname is still to be added.

| Team member | Primary ownership | Initial tasks and expected handoff |
|---|---|---|
| **Prachi Aswani** | Repository integration, acoustic preprocessing, feature engineering, PCA, K-means baseline, acoustic-only shared visuals, report integration | Implemented the validated acoustic long-to-wide loader, standardized 33-band matrix, PCA/K-means grid, metrics, and baseline plots. Shared temporal summaries and acoustic-only presentation media can be generated from the baseline assignments. Suggested branch: `prachi/acoustic-baseline`. |
| **Jacob Erard** | Animal-data audit, species and temporal-resolution documentation, GMM experiments, daily animal/state alignment, biological interpretation | Work is not included in this branch. Implement on the owner's branch and submit for review before integration. Suggested branch: `jacob/animal-gmm`. |
| **Parker [last name TBD]** | Vessel/weather audit, exact source and unit documentation, HDBSCAN or DBSCAN experiments, vessel/weather interpretation, unusual-event analysis | Work is not included in this branch. Implement on the owner's branch and submit for review before integration. Suggested branch: `parker/density-context`. |

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
