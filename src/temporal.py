from __future__ import annotations

import numpy as np
import pandas as pd


def summarize_state_dynamics(assignments: pd.DataFrame) -> dict[str, pd.DataFrame]:
    required = {"time", "deployment", "state"}
    if not required.issubset(assignments.columns):
        raise ValueError(f"Assignments require columns: {sorted(required)}")
    data = assignments.copy()
    data["time"] = pd.to_datetime(data["time"], errors="coerce", utc=True)
    if data["time"].isna().any() or data["state"].isna().any():
        raise ValueError("Assignments must contain valid timestamps and states.")
    data = data.sort_values(["deployment", "time"]).reset_index(drop=True)
    if data.duplicated(["deployment", "time"]).any():
        raise ValueError("Assignments contain duplicate deployment/hour keys.")

    previous_time = data.groupby("deployment")["time"].shift(1)
    previous_state = data.groupby("deployment")["state"].shift(1)
    data["contiguous"] = data["time"].sub(previous_time).eq(pd.Timedelta(hours=1))
    eligible = data["contiguous"]
    transitions = pd.crosstab(
        previous_state.loc[eligible].astype(int),
        data.loc[eligible, "state"].astype(int),
        dropna=False,
    )
    state_ids = sorted(data["state"].astype(int).unique())
    transitions = transitions.reindex(index=state_ids, columns=state_ids, fill_value=0)
    transitions.index.name = "from_state"
    transitions.columns.name = "to_state"
    probabilities = transitions.div(transitions.sum(axis=1).replace(0, np.nan), axis=0).fillna(0)
    probabilities.index.name = "from_state"
    probabilities.columns.name = "to_state"

    data["new_run"] = (
        data["state"].ne(previous_state)
        | ~data["contiguous"]
        | data["deployment"].ne(data["deployment"].shift(1))
    )
    data["run_id"] = data["new_run"].cumsum()
    runs = (
        data.groupby(["run_id", "deployment", "state"], as_index=False)
        .agg(
            start_utc=("time", "min"),
            end_utc=("time", "max"),
            observations=("state", "size"),
        )
    )
    runs["duration_hours"] = runs["observations"]
    duration_by_state = (
        runs.groupby("state", as_index=False)
        .agg(
            runs=("duration_hours", "size"),
            median_duration_hours=("duration_hours", "median"),
            mean_duration_hours=("duration_hours", "mean"),
            max_duration_hours=("duration_hours", "max"),
            p90_duration_hours=("duration_hours", lambda values: values.quantile(0.9)),
        )
    )
    transition_list = (
        transitions.stack()
        .rename("transitions")
        .reset_index()
        .query("transitions > 0")
        .sort_values("transitions", ascending=False)
    )
    transition_list["probability"] = transition_list.apply(
        lambda row: probabilities.loc[row["from_state"], row["to_state"]],
        axis=1,
    )
    row_sums = transitions.sum(axis=1).to_numpy(dtype=float)
    row_probabilities = probabilities.to_numpy(dtype=float)
    entropy_values = []
    for state, values, n in zip(state_ids, row_probabilities, row_sums):
        positive = values > 0
        entropy_values.append(
            {
                "state": state,
                "outgoing_transitions": int(n),
                "transition_entropy_nats": float(
                    -np.sum(values[positive] * np.log(values[positive]))
                ),
            }
        )

    data["hour_utc"] = data["time"].dt.hour
    data["month"] = data["time"].dt.strftime("%Y-%m")
    data["weekday"] = data["time"].dt.dayofweek
    data["day_type"] = np.where(data["weekday"] < 5, "weekday", "weekend")
    by_hour = (
        data.groupby(["hour_utc", "state"]).size().rename("observations").reset_index()
    )
    by_hour["fraction"] = by_hour["observations"] / by_hour.groupby("hour_utc")[
        "observations"
    ].transform("sum")
    by_month = (
        data.groupby(["month", "state"]).size().rename("observations").reset_index()
    )
    by_month["fraction"] = by_month["observations"] / by_month.groupby("month")[
        "observations"
    ].transform("sum")
    by_day_type = (
        data.groupby(["day_type", "state"])
        .size()
        .rename("observations")
        .reset_index()
    )
    by_day_type["fraction"] = by_day_type["observations"] / by_day_type.groupby(
        "day_type"
    )["observations"].transform("sum")

    return {
        "transition_counts": transitions,
        "transition_probabilities": probabilities,
        "duration_by_state": duration_by_state,
        "run_lengths": runs,
        "most_common_transitions": transition_list,
        "transition_entropy": pd.DataFrame(entropy_values),
        "state_by_hour": by_hour,
        "state_by_month": by_month,
        "state_by_day_type": by_day_type,
        "ordered_assignments": data,
    }
