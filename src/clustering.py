from __future__ import annotations

from itertools import combinations

import numpy as np
import pandas as pd
from sklearn import config_context
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import (
    adjusted_rand_score,
    davies_bouldin_score,
    silhouette_score,
)


def fit_pca_90(
    standardized_spectrum: np.ndarray,
    variance_threshold: float = 0.90,
) -> tuple[PCA, np.ndarray, pd.DataFrame]:
    """Fit full PCA and return the smallest leading-component representation."""
    if not 0 < variance_threshold <= 1:
        raise ValueError("variance_threshold must be in (0, 1].")
    if standardized_spectrum.ndim != 2 or standardized_spectrum.shape[0] < 2:
        raise ValueError("PCA requires a 2D matrix with at least two rows.")

    pca = PCA(svd_solver="full")
    scores = pca.fit_transform(standardized_spectrum)
    cumulative = np.cumsum(pca.explained_variance_ratio_)
    component_count = int(np.searchsorted(cumulative, variance_threshold) + 1)
    variance = pd.DataFrame(
        {
            "component": np.arange(1, len(cumulative) + 1),
            "explained_variance_ratio": pca.explained_variance_ratio_,
            "cumulative_explained_variance": cumulative,
        }
    )
    return pca, scores[:, :component_count], variance


def evaluate_kmeans_grid(
    representation: np.ndarray,
    *,
    cluster_counts: tuple[int, ...] = tuple(range(2, 9)),
    seeds: tuple[int, ...] = (42, 123, 2026),
    n_init: int = 10,
    silhouette_sample_size: int = 3000,
) -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    dict[tuple[int, int], KMeans],
    pd.DataFrame,
]:
    """Evaluate K-means using repeat seeds, sampled silhouette, DB score and ARI."""
    if representation.ndim != 2 or representation.shape[0] < 3:
        raise ValueError("K-means requires a 2D matrix with at least three rows.")
    if not seeds or not cluster_counts:
        raise ValueError("At least one seed and cluster count are required.")
    if any(k < 2 or k >= len(representation) for k in cluster_counts):
        raise ValueError("Each cluster count must be between 2 and n_samples - 1.")
    if silhouette_sample_size < 2:
        raise ValueError("silhouette_sample_size must be at least 2.")

    sample_size = min(silhouette_sample_size, len(representation))
    models: dict[tuple[int, int], KMeans] = {}
    labels_by_solution: dict[tuple[int, int], np.ndarray] = {}
    run_records: list[dict[str, float | int]] = []
    size_records: list[dict[str, float | int]] = []

    for k in cluster_counts:
        for seed in seeds:
            model = KMeans(
                n_clusters=k,
                random_state=seed,
                n_init=n_init,
                max_iter=300,
                algorithm="lloyd",
            )
            labels = model.fit_predict(representation)
            models[(k, seed)] = model
            labels_by_solution[(k, seed)] = labels
            counts = np.bincount(labels, minlength=k)
            with config_context(working_memory=16):
                silhouette = silhouette_score(
                    representation,
                    labels,
                    sample_size=sample_size,
                    random_state=42,
                )
            run_records.append(
                {
                    "k": k,
                    "seed": seed,
                    "inertia": float(model.inertia_),
                    "silhouette_sampled": float(silhouette),
                    "davies_bouldin": float(
                        davies_bouldin_score(representation, labels)
                    ),
                    "iterations": int(model.n_iter_),
                    "cluster_count": int(np.count_nonzero(counts)),
                }
            )
            size_records.extend(
                {
                    "k": k,
                    "seed": seed,
                    "cluster": cluster,
                    "observations": int(count),
                    "fraction": float(count / len(labels)),
                }
                for cluster, count in enumerate(counts)
            )

    runs = pd.DataFrame(run_records)
    pairwise_records = []
    for k in cluster_counts:
        for seed_a, seed_b in combinations(seeds, 2):
            pairwise_records.append(
                {
                    "k": k,
                    "seed_a": seed_a,
                    "seed_b": seed_b,
                    "adjusted_rand_index": float(
                        adjusted_rand_score(
                            labels_by_solution[(k, seed_a)],
                            labels_by_solution[(k, seed_b)],
                        )
                    ),
                }
            )
    stability = pd.DataFrame(pairwise_records)
    return runs, pd.DataFrame(size_records), models, stability


def summarize_kmeans_runs(runs: pd.DataFrame) -> pd.DataFrame:
    """Aggregate repeated-seed metrics without hiding per-run results."""
    summary = (
        runs.groupby("k", as_index=False)
        .agg(
            inertia_mean=("inertia", "mean"),
            inertia_std=("inertia", "std"),
            silhouette_mean=("silhouette_sampled", "mean"),
            silhouette_std=("silhouette_sampled", "std"),
            davies_bouldin_mean=("davies_bouldin", "mean"),
            davies_bouldin_std=("davies_bouldin", "std"),
            iterations_mean=("iterations", "mean"),
        )
        .sort_values("k")
    )
    return summary
