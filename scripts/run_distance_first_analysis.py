"""Mine daily acoustic patterns from explicit, competing distance functions.

The primary objects are complete 24-hour acoustic matrices.  This script does
not fit states using vessel, weather, calendar, or animal data. Those data are
only joined after acoustic motifs and outliers have been found.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from src.daily_similarity import (build_complete_daily_windows, daily_distance_matrix,
                                  motif_pairs, mutual_knn_components, nonoverlap_neighbors,
                                  outlier_table)
from src.data_loading import load_acoustic_spectrum
from src.features import build_interpretable_acoustic_features
from src.rhythm import contiguous_segments, daily_acoustic_frame, join_external_context

ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Distance-first daily acoustic motif and outlier analysis.")
    parser.add_argument("--input", type=Path, default=ROOT / "Data Mining Project" / "all.csv")
    parser.add_argument("--results-dir", type=Path, default=ROOT / "results" / "distance_first")
    parser.add_argument("--neighbors", type=int, default=10)
    parser.add_argument("--separation-days", type=int, default=14)
    return parser.parse_args()


def plot_motifs(matrices: np.ndarray, frequencies: tuple[float, ...], metadata: pd.DataFrame, motifs: pd.DataFrame, output: Path) -> None:
    if motifs.empty:
        return
    rows = min(3, len(motifs)); fig, axes = plt.subplots(rows, 2, figsize=(13, 3.2 * rows), squeeze=False)
    for row_index, (_, pair) in enumerate(motifs.head(rows).iterrows()):
        for column, (index, label) in enumerate([(int(pair.source_window_id), "first"), (int(pair.neighbor_window_id), "repeat")]):
            axis = axes[row_index, column]
            image = axis.imshow(matrices[index].T, aspect="auto", origin="lower", cmap="viridis")
            ticks = np.linspace(0, len(frequencies) - 1, min(6, len(frequencies)), dtype=int)
            axis.set_yticks(ticks, [f"{frequencies[tick]:g}" for tick in ticks])
            axis.set(title=f"Motif {int(pair.motif_rank)} {label}: {metadata.iloc[index].date.date()}", xlabel="Hour UTC", ylabel="Frequency (Hz)")
            fig.colorbar(image, ax=axis, label="Sound level")
    fig.suptitle("Closest non-overlapping daily motifs under shape-only distance")
    fig.tight_layout(); fig.savefig(output, dpi=180); plt.close(fig)


def plot_distance_comparison(level: np.ndarray, shape: np.ndarray, output: Path) -> None:
    upper = np.triu_indices_from(level, k=1); rng = np.random.default_rng(2026)
    sample = rng.choice(len(upper[0]), size=min(30_000, len(upper[0])), replace=False)
    fig, axis = plt.subplots(figsize=(7, 6))
    axis.scatter(level[upper][sample], shape[upper][sample], s=3, alpha=.15)
    axis.set(title="Two defensible daily-acoustic distances disagree usefully", xlabel="Level-sensitive RMS L2 distance", ylabel="Shape-only RMS L2 distance")
    fig.tight_layout(); fig.savefig(output, dpi=180); plt.close(fig)


def plot_graph_windows(metadata: pd.DataFrame, components: pd.DataFrame, outliers: pd.DataFrame, output: Path) -> None:
    data = metadata.merge(components, on="window_id").merge(outliers[["window_id", "mean_knn_distance", "outlier_rank"]], on="window_id")
    data["month"] = pd.to_datetime(data["date"], utc=True).dt.month
    fig, axis = plt.subplots(figsize=(10, 5))
    scatter = axis.scatter(data["month"], data["mean_knn_distance"], c=data["component_size"], cmap="plasma", s=18, alpha=.8)
    axis.scatter(data.nsmallest(10, "outlier_rank")["month"], data.nsmallest(10, "outlier_rank")["mean_knn_distance"], marker="x", color="black", label="top 10 outliers")
    axis.set(title="Mutual-kNN neighborhoods and isolated daily acoustic objects", xlabel="Month of year", ylabel="Mean distance to 10 nearest non-overlapping days")
    axis.legend(); fig.colorbar(scatter, ax=axis, label="Mutual-kNN component size")
    fig.tight_layout(); fig.savefig(output, dpi=180); plt.close(fig)


def feedback_summary(result: Path, windows: pd.DataFrame, level_motifs: pd.DataFrame, shape_motifs: pd.DataFrame, level_outliers: pd.DataFrame, shape_outliers: pd.DataFrame, agreement: float) -> None:
    def markdown_table(frame: pd.DataFrame) -> str:
        """Small dependency-free Markdown table writer for the feedback packet."""
        columns = list(frame.columns)
        rows = [[str(value) for value in row] for row in frame.itertuples(index=False, name=None)]
        return "\n".join([
            "| " + " | ".join(columns) + " |",
            "| " + " | ".join(["---"] * len(columns)) + " |",
            *["| " + " | ".join(row) + " |" for row in rows],
        ])

    lines = [
        "# Distance-first feedback packet for Jeff",
        "",
        "## The pivot",
        "",
        "We now treat one complete UTC day as one acoustic time-series object: a 24 x 33 matrix of observed sound levels. We mine structure by comparing these objects with explicit distances, rather than making PCA/K-means the central result.",
        "",
        "## Representations and distances",
        "",
        "1. **Level-sensitive representation:** each day is a 24 x 33 matrix; every frequency band is standardized over all observed hours, then the flattened daily matrices are compared with root-mean-square Euclidean distance. This preserves overall level and within-day evolution.",
        "2. **Shape-only representation:** each hour has its broadband mean subtracted before the same standardization and RMS Euclidean distance. This removes hour-to-hour overall loudness so it compares spectral shape instead.",
        "",
        "For flattened daily vectors `u` and `v` with `d = 24 x 33` entries, both reported distances use `sqrt(sum((u - v)^2) / d)`. The representation supplied to that formula is the deliberate modeling choice.",
        "",
        f"There are **{len(windows):,} complete, contiguous daily objects**. Candidate motif neighbors must be at least 14 calendar days apart, preventing a day from matching the day immediately before or after it.",
        "",
        "## What we mine from the distance",
        "",
        "- nearest non-overlapping neighbors: repeated daily motifs;",
        "- a mutual 10-nearest-neighbor graph: neighborhoods of days that select each other as similar;",
        "- mean distance to ten nearest historical days: isolated, acoustically unusual days.",
        "",
        "## Early concrete results",
        "",
        f"The rank-one nearest-neighbor agreement between the level-sensitive and shape-only representations is **{agreement:.1%}**. This disagreement is useful: it identifies days that are similar in loudness but not spectral shape, or vice versa.",
        "",
        "### Closest level-sensitive motifs",
        "",
        markdown_table(level_motifs.head(3)[["motif_rank", "source_date", "neighbor_date", "distance"]]),
        "",
        "### Closest shape-only motifs",
        "",
        markdown_table(shape_motifs.head(3)[["motif_rank", "source_date", "neighbor_date", "distance"]]),
        "",
        "### Most isolated daily objects under shape-only distance",
        "",
        markdown_table(shape_outliers.head(5)[["outlier_rank", "date", "deployment", "mean_knn_distance"]]),
        "",
        "## Questions for feedback",
        "",
        "1. Is a complete 24-hour acoustic matrix the right primary object, or should we also make a seven-day object the main unit?",
        "2. Is this two-distance comparison a sufficiently meaningful modeling comparison, before we add an optional time-series foundation-model embedding?",
        "3. Is the mutual-kNN graph plus nearest-neighbor motifs and outlier ranking the right notion of structure for this project?",
        "",
        "PCA/K-means and GMM remain baselines. Vessel, weather, and animal variables are held out of distance construction and used only after discovery to interpret selected motifs or unusual days.",
    ]
    (result / "JEFF_FEEDBACK_PACKET.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    options = parse_args(); result = options.results_dir; table_dir = result / "tables"; figure_dir = result / "figures"
    table_dir.mkdir(parents=True, exist_ok=True); figure_dir.mkdir(parents=True, exist_ok=True)
    dataset = load_acoustic_spectrum(options.input)
    windows = build_complete_daily_windows(dataset.observations, dataset.spectrum)
    level_distance = daily_distance_matrix(windows.level_vectors); shape_distance = daily_distance_matrix(windows.shape_vectors)
    np.savez_compressed(result / "daily_distance_matrices.npz", level_sensitive=level_distance, shape_only=shape_distance)
    level_neighbors = nonoverlap_neighbors(level_distance, windows.metadata, k=options.neighbors, separation_days=options.separation_days)
    shape_neighbors = nonoverlap_neighbors(shape_distance, windows.metadata, k=options.neighbors, separation_days=options.separation_days)
    level_motifs, shape_motifs = motif_pairs(level_neighbors), motif_pairs(shape_neighbors)
    components, _ = mutual_knn_components(shape_neighbors, len(windows.metadata), k=options.neighbors)
    level_outliers, shape_outliers = outlier_table(level_neighbors, windows.metadata, k=options.neighbors), outlier_table(shape_neighbors, windows.metadata, k=options.neighbors)
    agreement = (level_neighbors.query("neighbor_rank == 1").set_index("source_window_id")["neighbor_window_id"] == shape_neighbors.query("neighbor_rank == 1").set_index("source_window_id")["neighbor_window_id"]).mean()
    # Join external context only after distance-based discovery.
    hourly = pd.concat([dataset.observations, build_interpretable_acoustic_features(dataset.spectrum)], axis=1)
    hourly["segment_id"] = contiguous_segments(hourly); daily = daily_acoustic_frame(hourly)
    context, _, _ = join_external_context(daily, ROOT, None)
    shape_context = shape_outliers.merge(context, on="date", how="left")
    for name, frame in {"daily_windows": windows.metadata, "level_neighbors": level_neighbors, "shape_neighbors": shape_neighbors, "level_motifs": level_motifs, "shape_motifs": shape_motifs, "mutual_knn_components": components, "level_outliers": level_outliers, "shape_outliers": shape_outliers, "shape_outlier_context": shape_context}.items():
        frame.to_csv(table_dir / f"{name}.csv", index=False)
    plot_motifs(windows.raw_matrices, dataset.frequencies, windows.metadata, shape_motifs, figure_dir / "shape_only_daily_motifs.png")
    plot_distance_comparison(level_distance, shape_distance, figure_dir / "distance_choice_comparison.png")
    plot_graph_windows(windows.metadata, components, shape_outliers, figure_dir / "mutual_knn_graph_summary.png")
    feedback_summary(result, windows.metadata, level_motifs, shape_motifs, level_outliers, shape_outliers, agreement)
    print(f"Complete daily objects: {len(windows.metadata):,}")
    print(f"Level/shape rank-one neighbor agreement: {agreement:.1%}")
    print(f"Wrote distance-first analysis to {result}")


if __name__ == "__main__":
    main()
