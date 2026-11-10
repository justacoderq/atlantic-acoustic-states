"""Distance-first representations for daily acoustic time-series objects.

The unit of analysis is a complete, contiguous UTC day from one deployment.
Each object is a 24 x frequency-band matrix.  The two representations below
make different scientific claims and are intentionally kept separate:

* level: preserves absolute band levels and their daily evolution;
* shape: subtracts each hour's broadband mean, so it compares spectral shape
  rather than whether one day is simply louder than another.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components
from sklearn.metrics import pairwise_distances
from sklearn.preprocessing import StandardScaler


@dataclass(frozen=True)
class DailyWindows:
    metadata: pd.DataFrame
    level_vectors: np.ndarray
    shape_vectors: np.ndarray
    raw_matrices: np.ndarray


def build_complete_daily_windows(observations: pd.DataFrame, spectrum: pd.DataFrame) -> DailyWindows:
    """Create 24-hour acoustic objects without crossing gaps or deployments."""
    if len(observations) != len(spectrum):
        raise ValueError("Observations and spectrum must be row-aligned.")
    data = observations[["time", "deployment"]].copy()
    data["time"] = pd.to_datetime(data["time"], utc=True)
    data["date"] = data["time"].dt.floor("D")
    accepted: list[tuple[pd.Timestamp, str, np.ndarray]] = []
    for (date, deployment), group in data.groupby(["date", "deployment"], sort=True):
        indices = group.index.to_numpy()
        times = group["time"].sort_values().to_numpy()
        if len(indices) != 24:
            continue
        if not np.all(np.diff(times).astype("timedelta64[h]").astype(int) == 1):
            continue
        ordered = group.sort_values("time").index.to_numpy()
        accepted.append((date, str(deployment), ordered))
    if not accepted:
        raise ValueError("No complete contiguous 24-hour windows were found.")
    matrices = np.stack([spectrum.iloc[index].to_numpy(float) for _, _, index in accepted])
    metadata = pd.DataFrame(
        {
            "window_id": np.arange(len(accepted), dtype=int),
            "date": [date for date, _, _ in accepted],
            "deployment": [deployment for _, deployment, _ in accepted],
        }
    )
    # Standardize each acoustic band over observed hours, then retain the 24 h order.
    level_hours = StandardScaler().fit_transform(spectrum.to_numpy(float))
    level_vectors = np.stack([level_hours[index].ravel() for _, _, index in accepted])
    # Remove the hourly broadband level before standardizing frequency-shape values.
    shape_hours = spectrum.to_numpy(float)
    shape_hours = shape_hours - shape_hours.mean(axis=1, keepdims=True)
    shape_hours = StandardScaler().fit_transform(shape_hours)
    shape_vectors = np.stack([shape_hours[index].ravel() for _, _, index in accepted])
    return DailyWindows(metadata, level_vectors, shape_vectors, matrices)


def daily_distance_matrix(vectors: np.ndarray) -> np.ndarray:
    """Root-mean-square Euclidean distance between fixed-length daily objects."""
    if vectors.ndim != 2 or len(vectors) < 2:
        raise ValueError("Expected at least two flattened daily vectors.")
    return pairwise_distances(vectors, metric="euclidean") / np.sqrt(vectors.shape[1])


def nonoverlap_neighbors(distance: np.ndarray, metadata: pd.DataFrame, *, k: int = 10, separation_days: int = 14) -> pd.DataFrame:
    """Return the nearest historical days, excluding nearby calendar neighbors."""
    dates = pd.to_datetime(metadata["date"], utc=True)
    rows = []
    for source in range(len(metadata)):
        candidates = np.argsort(distance[source], kind="stable")
        chosen = 0
        for target in candidates:
            if source == target or abs((dates.iloc[source] - dates.iloc[target]).days) < separation_days:
                continue
            rows.append(
                {
                    "source_window_id": source,
                    "neighbor_rank": chosen + 1,
                    "neighbor_window_id": int(target),
                    "distance": float(distance[source, target]),
                    "source_date": dates.iloc[source],
                    "neighbor_date": dates.iloc[target],
                    "source_deployment": metadata.iloc[source]["deployment"],
                    "neighbor_deployment": metadata.iloc[target]["deployment"],
                }
            )
            chosen += 1
            if chosen == k:
                break
    return pd.DataFrame(rows)


def motif_pairs(neighbors: pd.DataFrame, *, count: int = 10) -> pd.DataFrame:
    """Choose non-redundant closest pairs from rank-one nearest neighbors."""
    rank_one = neighbors.loc[neighbors["neighbor_rank"].eq(1)].sort_values("distance")
    used: set[int] = set()
    selected = []
    for _, row in rank_one.iterrows():
        first, second = int(row["source_window_id"]), int(row["neighbor_window_id"])
        if first in used or second in used:
            continue
        used.update({first, second})
        selected.append({"motif_rank": len(selected) + 1, **row.to_dict()})
        if len(selected) == count:
            break
    return pd.DataFrame(selected)


def mutual_knn_components(neighbors: pd.DataFrame, n_windows: int, *, k: int = 10) -> tuple[pd.DataFrame, csr_matrix]:
    """Build a mutual-kNN graph and label its connected dense neighborhoods."""
    selected = neighbors.loc[neighbors["neighbor_rank"].le(k)]
    directed = {(int(row.source_window_id), int(row.neighbor_window_id)): float(row.distance) for row in selected.itertuples()}
    edges = [(left, right, value) for (left, right), value in directed.items() if (right, left) in directed]
    if not edges:
        graph = csr_matrix((n_windows, n_windows))
        labels = np.arange(n_windows)
    else:
        source = [edge[0] for edge in edges] + [edge[1] for edge in edges]
        target = [edge[1] for edge in edges] + [edge[0] for edge in edges]
        weights = [1.0 / (edge[2] + 1e-9) for edge in edges] * 2
        graph = csr_matrix((weights, (source, target)), shape=(n_windows, n_windows))
        _, labels = connected_components(graph, directed=False)
    sizes = pd.Series(labels).value_counts().to_dict()
    output = pd.DataFrame({"window_id": np.arange(n_windows), "mutual_knn_component": labels})
    output["component_size"] = output["mutual_knn_component"].map(sizes).astype(int)
    return output, graph


def outlier_table(neighbors: pd.DataFrame, metadata: pd.DataFrame, *, k: int = 10) -> pd.DataFrame:
    """Higher mean distance to k nearest non-overlapping days means more unusual."""
    summary = neighbors.loc[neighbors["neighbor_rank"].le(k)].groupby("source_window_id").agg(
        nearest_neighbor_distance=("distance", "min"),
        mean_knn_distance=("distance", "mean"),
        median_knn_distance=("distance", "median"),
    ).reset_index().rename(columns={"source_window_id": "window_id"})
    output = metadata.merge(summary, on="window_id", how="left")
    output["outlier_rank"] = output["mean_knn_distance"].rank(ascending=False, method="first").astype(int)
    return output.sort_values("outlier_rank").reset_index(drop=True)

