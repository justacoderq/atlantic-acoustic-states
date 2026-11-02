from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from src.clustering import evaluate_kmeans_grid, fit_pca_90, summarize_kmeans_runs
from src.data_loading import load_acoustic_spectrum
from src.features import build_interpretable_acoustic_features
from src.preprocessing import standardize_acoustic_spectrum


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "Data Mining Project" / "all.csv"
DEFAULT_PROCESSED = ROOT / "data" / "processed"
DEFAULT_RESULTS = ROOT / "results"
K_VALUES = tuple(range(2, 9))
RANDOM_SEEDS = (42, 123, 2026)
KMEANS_N_INIT = 10


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the acoustic PCA/K-means baseline and save reproducible outputs."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--processed-dir", type=Path, default=DEFAULT_PROCESSED)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--silhouette-sample-size", type=int, default=3000)
    return parser.parse_args()


def save_figures(
    *,
    variance: pd.DataFrame,
    summary: pd.DataFrame,
    profiles: pd.DataFrame,
    assignments: pd.DataFrame,
    hour_distribution: pd.DataFrame,
    figure_dir: Path,
) -> None:
    figure_dir.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid")

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(
        variance["component"],
        variance["cumulative_explained_variance"],
        marker="o",
        markersize=3,
    )
    ax.axhline(0.90, color="tab:red", linestyle="--", label="90% threshold")
    ax.set(
        xlabel="Principal component",
        ylabel="Cumulative explained variance",
        ylim=(0, 1.02),
        title="PCA explained variance: standardized acoustic spectrum",
    )
    ax.set_xlim(left=1)
    ax.legend()
    fig.tight_layout()
    fig.savefig(figure_dir / "pca_explained_variance.png", dpi=180)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    axes[0].errorbar(
        summary["k"],
        summary["inertia_mean"],
        yerr=summary["inertia_std"].fillna(0),
        marker="o",
        capsize=3,
    )
    axes[0].set(xlabel="Number of clusters (k)", ylabel="Inertia", title="Elbow")
    axes[1].errorbar(
        summary["k"],
        summary["silhouette_mean"],
        yerr=summary["silhouette_std"].fillna(0),
        marker="o",
        capsize=3,
    )
    axes[1].set(
        xlabel="Number of clusters (k)",
        ylabel="Silhouette (sampled)",
        title="Mean silhouette across seeds",
    )
    fig.suptitle("K-means model selection (error bars: seed standard deviation)")
    fig.tight_layout()
    fig.savefig(figure_dir / "kmeans_selection.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(12, 6))
    frequencies = np.asarray(
        [
            float(column.removeprefix("sound_").removesuffix("Hz"))
            for column in profiles.columns
        ]
    )
    for cluster, row in profiles.iterrows():
        values = row.to_numpy(dtype=float)
        ax.plot(frequencies, values, marker=".", linewidth=1.5, label=f"State {cluster}")
    ax.set_xscale("log")
    tick_frequencies = np.asarray(
        [13, 20, 50, 100, 250, 500, 1000, 2000, 5000, 10000, 20000],
        dtype=float,
    )
    ax.set_xticks(tick_frequencies, labels=[f"{frequency:g}" for frequency in tick_frequencies])
    ax.set(
        xlabel="Frequency (Hz, log scale)",
        ylabel="Median sound pressure level (source units)",
        title="Median acoustic profile by K-means state",
    )
    ax.legend(ncol=2)
    fig.tight_layout()
    fig.savefig(figure_dir / "kmeans_acoustic_profiles.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(13, 4))
    plot_data = assignments.copy()
    plot_data["time"] = pd.to_datetime(plot_data["time"], utc=True)
    ax.scatter(
        plot_data["time"],
        plot_data["state"],
        c=plot_data["state"],
        cmap="tab10",
        s=4,
        linewidths=0,
        rasterized=True,
    )
    ax.set(
        xlabel="Time (UTC)",
        ylabel="State identifier",
        yticks=sorted(plot_data["state"].unique()),
        title="Acoustic states over time (points only; gaps are not connected)",
    )
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(figure_dir / "kmeans_state_timeline.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 5))
    hour_pivot = hour_distribution.pivot(
        index="hour_utc", columns="state", values="fraction"
    )
    sns.heatmap(hour_pivot, cmap="viridis", vmin=0, vmax=1, ax=ax)
    ax.set(
        xlabel="State identifier",
        ylabel="Hour of day (UTC)",
        title="State fraction by hour of day",
    )
    fig.tight_layout()
    fig.savefig(figure_dir / "kmeans_state_by_hour.png", dpi=180)
    plt.close(fig)


def main() -> None:
    args = parse_args()
    if not args.input.is_file():
        raise FileNotFoundError(f"Acoustic input not found: {args.input}")

    processed_dir = args.processed_dir
    results_dir = args.results_dir
    table_dir = results_dir / "tables"
    assignment_dir = results_dir / "cluster_assignments"
    processed_dir.mkdir(parents=True, exist_ok=True)
    table_dir.mkdir(parents=True, exist_ok=True)
    assignment_dir.mkdir(parents=True, exist_ok=True)

    dataset = load_acoustic_spectrum(args.input)
    standardized, _ = standardize_acoustic_spectrum(dataset.spectrum)
    interpretable_features = build_interpretable_acoustic_features(dataset.spectrum)
    _, pca_scores, variance = fit_pca_90(standardized)
    runs, cluster_sizes, models, stability = evaluate_kmeans_grid(
        pca_scores,
        cluster_counts=K_VALUES,
        seeds=RANDOM_SEEDS,
        n_init=KMEANS_N_INIT,
        silhouette_sample_size=args.silhouette_sample_size,
    )
    summary = summarize_kmeans_runs(runs)
    stability_summary = (
        stability.groupby("k", as_index=False)
        .agg(
            adjusted_rand_mean=("adjusted_rand_index", "mean"),
            adjusted_rand_std=("adjusted_rand_index", "std"),
        )
    )
    summary = summary.merge(stability_summary, on="k", how="left")
    selected_k = int(
        summary.sort_values(
            ["silhouette_mean", "k"], ascending=[False, True]
        ).iloc[0]["k"]
    )
    selected_seed = min(
        RANDOM_SEEDS,
        key=lambda seed: models[(selected_k, seed)].inertia_,
    )
    selected_model = models[(selected_k, selected_seed)]
    labels = selected_model.labels_

    observations = dataset.observations.copy()
    assignments = observations.copy()
    assignments["state"] = labels
    profiles = (
        dataset.spectrum.assign(state=labels)
        .groupby("state")
        .median()
        .sort_index()
    )
    profiles.index.name = "state"
    profile_long = profiles.rename_axis("state").reset_index().melt(
        id_vars="state", var_name="frequency_band", value_name="median_level"
    )

    assignments["time"] = pd.to_datetime(assignments["time"], utc=True)
    assignments["hour_utc"] = assignments["time"].dt.hour
    hourly_counts = (
        assignments.groupby(["hour_utc", "state"]).size().rename("observations").reset_index()
    )
    hourly_counts["fraction"] = hourly_counts["observations"] / hourly_counts.groupby(
        "hour_utc"
    )["observations"].transform("sum")

    observations.to_csv(processed_dir / "acoustic_observations.csv", index=False)
    pd.DataFrame(standardized, columns=dataset.spectrum.columns).to_csv(
        processed_dir / "acoustic_feature_matrix_standardized.csv", index=False
    )
    interpretable_features.to_csv(
        processed_dir / "acoustic_interpretable_features.csv", index=False
    )
    variance.to_csv(table_dir / "pca_explained_variance.csv", index=False)
    runs.to_csv(table_dir / "kmeans_runs.csv", index=False)
    summary.to_csv(table_dir / "kmeans_summary.csv", index=False)
    cluster_sizes.to_csv(table_dir / "kmeans_cluster_sizes.csv", index=False)
    stability.to_csv(table_dir / "kmeans_seed_stability.csv", index=False)
    profiles.to_csv(table_dir / "kmeans_median_profiles.csv")
    profile_long.to_csv(table_dir / "kmeans_median_profiles_long.csv", index=False)
    hourly_counts.to_csv(table_dir / "kmeans_state_by_hour.csv", index=False)
    assignments.drop(columns="hour_utc").to_csv(
        assignment_dir / "kmeans_selected_assignments.csv", index=False
    )

    metrics = pd.DataFrame(
        [
            {"metric": "input_rows_long", "value": dataset.source_rows},
            {"metric": "hourly_observations", "value": len(dataset.spectrum)},
            {"metric": "frequency_bands", "value": len(dataset.frequencies)},
            {"metric": "deployments", "value": dataset.observations["deployment"].nunique()},
            {"metric": "first_observation_utc", "value": dataset.observations["time"].min()},
            {"metric": "last_observation_utc", "value": dataset.observations["time"].max()},
            {"metric": "pca_components_for_90_percent", "value": pca_scores.shape[1]},
            {"metric": "pca_variance_retained", "value": float(variance.iloc[pca_scores.shape[1] - 1]["cumulative_explained_variance"])},
            {"metric": "silhouette_sample_size", "value": min(args.silhouette_sample_size, len(pca_scores))},
            {"metric": "k_values_tested", "value": ",".join(map(str, K_VALUES))},
            {"metric": "random_seeds", "value": ",".join(map(str, RANDOM_SEEDS))},
            {"metric": "n_init_per_seed", "value": KMEANS_N_INIT},
            {"metric": "selected_k_by_mean_sampled_silhouette", "value": selected_k},
            {"metric": "selected_seed_lowest_inertia_at_selected_k", "value": selected_seed},
            {"metric": "selected_solution_inertia", "value": float(selected_model.inertia_)},
        ]
    )
    metrics.to_csv(table_dir / "baseline_run_metadata.csv", index=False)
    selected_summary = summary.loc[summary["k"].eq(selected_k)].iloc[0]
    selected_sizes = cluster_sizes.loc[
        cluster_sizes["k"].eq(selected_k)
        & cluster_sizes["seed"].eq(selected_seed)
    ]
    try:
        input_label = args.input.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        input_label = args.input.name
    summary_lines = [
        "# Acoustic PCA/K-means baseline summary",
        "",
        "Generated by `python -m scripts.run_acoustic_baseline` from the included acoustic CSV.",
        "",
        f"- Input: `{input_label}`",
        f"- Long rows: {dataset.source_rows:,}",
        f"- Hourly acoustic observations: {len(dataset.spectrum):,}",
        f"- Frequency bands: {len(dataset.frequencies)}",
        f"- Deployments: {dataset.observations['deployment'].nunique()}",
        f"- Observed range: {dataset.observations['time'].min()} to {dataset.observations['time'].max()}",
        f"- PCA components to reach 90%: {pca_scores.shape[1]}",
        f"- Cumulative variance retained: {variance.iloc[pca_scores.shape[1] - 1]['cumulative_explained_variance']:.6f}",
        f"- K-means grid: k={K_VALUES[0]}..{K_VALUES[-1]}, seeds={RANDOM_SEEDS}, n_init={KMEANS_N_INIT}",
        f"- Silhouette uses a fixed random sample of {min(args.silhouette_sample_size, len(pca_scores)):,} observations.",
        f"- Selected k by highest mean sampled silhouette: {selected_k}",
        f"- Selected assignment seed (lowest inertia at this k): {selected_seed}",
        f"- Selected solution inertia: {selected_model.inertia_:.3f}",
        f"- Selected-k mean sampled silhouette across seeds: {selected_summary['silhouette_mean']:.6f} (SD {selected_summary['silhouette_std']:.6f})",
        f"- Selected-k mean Davies-Bouldin score: {selected_summary['davies_bouldin_mean']:.6f}",
        f"- Selected-k mean pairwise seed ARI: {selected_summary['adjusted_rand_mean']:.6f}",
        "",
        "Selected assignment cluster sizes:",
        "",
        "| State ID | Observations | Fraction |",
        "|---:|---:|---:|",
    ]
    summary_lines.extend(
        f"| {int(row.cluster)} | {int(row.observations):,} | {row.fraction:.4%} |"
        for row in selected_sizes.itertuples(index=False)
    )
    summary_lines.extend(
        [
            "",
            "## Mean metrics by k",
            "",
            "| k | Inertia | Sampled silhouette | Davies-Bouldin | Mean seed ARI |",
            "|---:|---:|---:|---:|---:|",
        ]
    )
    summary_lines.extend(
        f"| {int(row.k)} | {row.inertia_mean:.3f} | {row.silhouette_mean:.6f} | "
        f"{row.davies_bouldin_mean:.6f} | {row.adjusted_rand_mean:.6f} |"
        for row in summary.itertuples(index=False)
    )
    summary_lines.extend(
        [
            "",
            "These are descriptive baseline metrics, not scientific labels or causal conclusions.",
            "See `docs/PRACHI_ACOUSTIC_BASELINE.md` for method and interpretation limits.",
        ]
    )
    log_dir = results_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    (log_dir / "acoustic_baseline_summary.md").write_text(
        "\n".join(summary_lines) + "\n", encoding="utf-8"
    )
    save_figures(
        variance=variance,
        summary=summary,
        profiles=profiles,
        assignments=assignments,
        hour_distribution=hourly_counts,
        figure_dir=results_dir / "figures",
    )

    print(f"Acoustic observations: {len(dataset.spectrum):,}")
    print(f"Frequency bands: {len(dataset.frequencies)}")
    print(f"PCA components retaining 90% variance: {pca_scores.shape[1]}")
    print(f"Selected k (highest mean sampled silhouette): {selected_k}")
    print(f"Selected seed (lowest inertia for k): {selected_seed}")
    print(
        summary[
            ["k", "inertia_mean", "silhouette_mean", "davies_bouldin_mean", "adjusted_rand_mean"]
        ].to_string(index=False)
    )
    print(f"Outputs saved under {processed_dir} and {results_dir}")


if __name__ == "__main__":
    main()
