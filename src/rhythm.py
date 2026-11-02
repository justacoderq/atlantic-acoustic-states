"""Gap-aware temporal discovery tools for the Stellwagen acoustic time series.

The functions in this module deliberately fit only acoustic measurements.
Ship, weather, animal, and calendar variables are joined afterwards for
descriptive context; they never determine a state, motif, change point, or
anomaly score.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


FEATURE_COLUMNS = [
    "low_mean_level_le_250hz",
    "mid_mean_level_250_2000hz",
    "high_mean_level_gt_2000hz",
    "broadband_mean_level",
    "spectral_slope_per_log10_hz",
    "normalized_spectral_entropy",
]


def contiguous_segments(observations: pd.DataFrame) -> pd.Series:
    """Return a segment id that changes at every gap or deployment boundary."""
    data = observations.copy()
    data["time"] = pd.to_datetime(data["time"], utc=True)
    previous_time = data.groupby("deployment")["time"].shift()
    contiguous = data["time"].sub(previous_time).eq(pd.Timedelta(hours=1))
    return (~contiguous).cumsum().astype(int)


def periodicity_table(hourly: pd.DataFrame, max_lag_hours: int = 24 * 30) -> pd.DataFrame:
    """Autocorrelation by acoustic feature, averaged only within valid segments."""
    rows: list[dict[str, float | int | str]] = []
    for feature in FEATURE_COLUMNS:
        values = hourly[["segment_id", feature]].copy()
        for lag in range(1, max_lag_hours + 1):
            correlations = []
            weights = []
            for _, segment in values.groupby("segment_id", sort=False):
                series = segment[feature].to_numpy(float)
                if len(series) <= lag:
                    continue
                left, right = series[:-lag], series[lag:]
                if np.std(left) and np.std(right):
                    correlations.append(float(np.corrcoef(left, right)[0, 1]))
                    weights.append(len(left))
            rows.append(
                {
                    "feature": feature,
                    "lag_hours": lag,
                    "autocorrelation": float(np.average(correlations, weights=weights))
                    if correlations
                    else np.nan,
                    "pairs": int(sum(weights)),
                }
            )
    return pd.DataFrame(rows)


def daily_acoustic_frame(hourly: pd.DataFrame) -> pd.DataFrame:
    """Daily observed acoustic summaries; partial days remain explicitly marked."""
    data = hourly.copy()
    data["date"] = pd.to_datetime(data["time"], utc=True).dt.floor("D")
    means = data.groupby("date", as_index=False)[FEATURE_COLUMNS].mean()
    metadata = data.groupby("date", as_index=False).agg(
        acoustic_hours=("time", "size"),
        deployments=("deployment", lambda x: "+".join(sorted(set(x)))),
        segment_id=("segment_id", "first"),
    )
    daily = means.merge(metadata, on="date", how="inner")
    daily["keep_day"] = daily["acoustic_hours"] >= 20
    return daily


def detect_change_points(daily: pd.DataFrame, window_days: int = 7, min_spacing_days: int = 14) -> pd.DataFrame:
    """Rank abrupt daily acoustic shifts with a symmetric rolling-window score."""
    values = daily.loc[daily["keep_day"], FEATURE_COLUMNS].to_numpy(float)
    scaled = StandardScaler().fit_transform(values)
    kept = daily.loc[daily["keep_day"]].copy().reset_index(drop=True)
    score = np.full(len(kept), np.nan)
    for index in range(window_days, len(kept) - window_days):
        # Never compare across a date gap or a deployment boundary.
        dates = kept.loc[index - window_days : index + window_days, "date"]
        if not dates.diff().dropna().eq(pd.Timedelta(days=1)).all():
            continue
        if kept.loc[index - window_days : index + window_days, "deployments"].nunique() != 1:
            continue
        score[index] = np.linalg.norm(
            scaled[index - window_days : index].mean(axis=0)
            - scaled[index : index + window_days].mean(axis=0)
        )
    kept["change_score"] = score
    candidates = kept.dropna(subset=["change_score"]).sort_values("change_score", ascending=False)
    selected = []
    for _, row in candidates.iterrows():
        if all(abs((row["date"] - chosen["date"]).days) >= min_spacing_days for chosen in selected):
            selected.append(row)
    result = pd.DataFrame(selected).sort_values("date") if selected else kept.iloc[0:0]
    return result.reset_index(drop=True)


def anomaly_scores(daily: pd.DataFrame, changes: pd.DataFrame, random_state: int = 2026) -> pd.DataFrame:
    """Daily acoustic outlier score, with change evidence retained separately."""
    result = daily.copy()
    usable = result["keep_day"]
    model = IsolationForest(contamination="auto", random_state=random_state, n_estimators=300)
    model.fit(result.loc[usable, FEATURE_COLUMNS])
    # Larger values mean more anomalous, which is easier to communicate.
    result["acoustic_anomaly_score"] = np.nan
    result.loc[usable, "acoustic_anomaly_score"] = -model.score_samples(result.loc[usable, FEATURE_COLUMNS])
    change_lookup = changes.set_index("date")["change_score"] if len(changes) else pd.Series(dtype=float)
    result["change_score"] = result["date"].map(change_lookup).fillna(0.0)
    normalized_anomaly = (result["acoustic_anomaly_score"] - result["acoustic_anomaly_score"].mean()) / result["acoustic_anomaly_score"].std()
    normalized_change = (result["change_score"] - result["change_score"].mean()) / result["change_score"].std()
    result["combined_unusualness"] = normalized_anomaly.fillna(0) + normalized_change.fillna(0)
    return result


def discover_motifs(daily: pd.DataFrame, window_days: int = 7, maximum_candidates: int = 400) -> pd.DataFrame:
    """Find repeated week-long multivariate patterns without bridging gaps.

    This is an intentionally transparent sampled matrix-profile approximation:
    all candidate subsequences are standardized feature windows and each sampled
    window is paired with its nearest non-overlapping candidate in the same
    contiguous deployment segment.
    """
    usable = daily.loc[daily["keep_day"]].copy().reset_index(drop=True)
    usable["daily_segment"] = (
        usable["date"].diff().ne(pd.Timedelta(days=1))
        | usable["deployments"].ne(usable["deployments"].shift())
    ).cumsum()
    windows: list[dict[str, object]] = []
    for segment_id, segment in usable.groupby("daily_segment", sort=False):
        if len(segment) < window_days * 2:
            continue
        scaled = StandardScaler().fit_transform(segment[FEATURE_COLUMNS])
        for start in range(0, len(segment) - window_days + 1):
            windows.append(
                {
                    "daily_segment": int(segment_id),
                    "start": start,
                    "start_date": segment.iloc[start]["date"],
                    "end_date": segment.iloc[start + window_days - 1]["date"],
                    "vector": scaled[start : start + window_days].ravel(),
                }
            )
    if not windows:
        return pd.DataFrame(columns=["motif_rank", "first_start_utc", "second_start_utc", "distance"])
    candidate_indices = np.linspace(0, len(windows) - 1, min(maximum_candidates, len(windows)), dtype=int)
    pairs = []
    for index in candidate_indices:
        item = windows[index]
        best: tuple[float, dict[str, object]] | None = None
        for other in windows:
            if other["daily_segment"] != item["daily_segment"] or abs(int(other["start"]) - int(item["start"])) < window_days:
                continue
            distance = float(np.mean((item["vector"] - other["vector"]) ** 2) ** 0.5)
            if best is None or distance < best[0]:
                best = (distance, other)
        if best:
            pairs.append((best[0], item, best[1]))
    pairs.sort(key=lambda pair: pair[0])
    chosen = []
    used_dates: set[pd.Timestamp] = set()
    for distance, first, second in pairs:
        starts = {first["start_date"], second["start_date"]}
        if starts & used_dates:
            continue
        used_dates.update(starts)
        chosen.append(
            {
                "motif_rank": len(chosen) + 1,
                "window_days": window_days,
                "first_start_utc": first["start_date"],
                "first_end_utc": first["end_date"],
                "second_start_utc": second["start_date"],
                "second_end_utc": second["end_date"],
                "distance": distance,
            }
        )
        if len(chosen) == 10:
            break
    return pd.DataFrame(chosen)


def join_external_context(daily: pd.DataFrame, root: Path, assignments: pd.DataFrame | None) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Attach available external context after acoustic discovery, never before."""
    context = daily.copy()
    project = root / "Data Mining Project"
    ships = pd.read_csv(project / "ships_hourly.csv")
    ships["time"] = pd.to_datetime(ships["hour_utc"], utc=True)
    ships["date"] = ships["time"].dt.floor("D")
    ship_daily = ships.groupby("date", as_index=False).agg(ship_minutes_mean=("ship_minutes", "mean"), ship_present_fraction=("ship_present", "mean"))
    context = context.merge(ship_daily, on="date", how="left")
    weather = pd.read_csv(project / "weather_hourly.csv")
    weather["date"] = pd.to_datetime(weather["hour_utc"], utc=True).dt.floor("D")
    weather_columns = [column for column in weather.columns if column not in {"hour_utc", "date", "Unnamed: 0"}]
    context = context.merge(weather.groupby("date", as_index=False)[weather_columns].mean(), on="date", how="left")
    animals_path = root / "data" / "processed" / "animals_daily.csv"
    if animals_path.exists():
        animals = pd.read_csv(animals_path, parse_dates=["date"])
        animals["date"] = pd.to_datetime(animals["date"], utc=True)
        animal_wide = animals.pivot(index="date", columns="animal", values="presence").add_prefix("animal_").reset_index()
        context = context.merge(animal_wide, on="date", how="left")
    state_summary = pd.DataFrame()
    animal_state = pd.DataFrame()
    if assignments is not None and not assignments.empty:
        states = assignments.copy()
        states["time"] = pd.to_datetime(states["time"], utc=True)
        states["date"] = states["time"].dt.floor("D")
        state_day = states.groupby("date")["state"].agg(lambda x: int(x.mode().iloc[0])).rename("daily_majority_state").reset_index()
        context = context.merge(state_day, on="date", how="left")
        numeric_context = ["ship_minutes_mean", "ship_present_fraction"] + weather_columns
        state_summary = context.groupby("daily_majority_state")[numeric_context].mean().reset_index()
        animal_columns = [column for column in context if column.startswith("animal_")]
        if animal_columns:
            animal_state = context.groupby("daily_majority_state")[animal_columns].mean().reset_index()
    return context, state_summary, animal_state
