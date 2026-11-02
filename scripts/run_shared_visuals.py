from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from src.data_loading import load_acoustic_spectrum
from src.poster_visuals import (
    create_heartbeat_animation,
    create_poster_snapshot,
    create_state_tone_sonification,
)
from src.temporal import summarize_state_dynamics


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate acoustic-only temporal summaries and presentation visuals."
    )
    parser.add_argument("--input", type=Path, default=ROOT / "Data Mining Project" / "all.csv")
    parser.add_argument(
        "--assignments",
        type=Path,
        default=ROOT / "results" / "cluster_assignments" / "kmeans_selected_assignments.csv",
    )
    parser.add_argument("--results-dir", type=Path, default=ROOT / "results")
    parser.add_argument("--skip-animation", action="store_true")
    parser.add_argument("--skip-sonification", action="store_true")
    return parser.parse_args()


def save_heatmap(
    frame: pd.DataFrame,
    output_path: Path,
    title: str,
    *,
    cmap: str = "viridis",
    annotate: bool = False,
) -> None:
    fig, axis = plt.subplots(figsize=(11, 6))
    sns.heatmap(
        frame,
        cmap=cmap,
        vmin=0,
        vmax=1,
        annot=annotate,
        fmt=".2f",
        ax=axis,
    )
    axis.set_title(title)
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def validate_assignment_alignment(
    assignments: pd.DataFrame,
    observations: pd.DataFrame,
) -> pd.DataFrame:
    required = {"time", "deployment", "state"}
    missing = required.difference(assignments.columns)
    if missing:
        raise ValueError(f"Assignments are missing columns: {sorted(missing)}")
    if len(assignments) != len(observations):
        raise ValueError(
            "Assignment count does not match the acoustic input; rerun the acoustic baseline."
        )

    aligned = assignments.copy()
    assigned_times = pd.to_datetime(aligned["time"], errors="coerce", utc=True)
    source_times = pd.to_datetime(observations["time"], errors="coerce", utc=True)
    if assigned_times.isna().any() or source_times.isna().any():
        raise ValueError("Assignments and acoustic observations must have valid timestamps.")
    if not assigned_times.reset_index(drop=True).equals(source_times.reset_index(drop=True)):
        raise ValueError(
            "Assignment timestamps do not match the acoustic input; rerun the acoustic baseline."
        )
    if not aligned["deployment"].astype(str).reset_index(drop=True).equals(
        observations["deployment"].astype(str).reset_index(drop=True)
    ):
        raise ValueError(
            "Assignment deployments do not match the acoustic input; rerun the acoustic baseline."
        )
    if aligned["state"].isna().any():
        raise ValueError("Assignments contain missing state labels.")

    aligned["time"] = assigned_times
    aligned["state"] = aligned["state"].astype(int)
    return aligned


def main() -> None:
    args = parse_args()
    if not args.input.is_file():
        raise FileNotFoundError(f"Acoustic input not found: {args.input}")
    if not args.assignments.is_file():
        raise FileNotFoundError(
            f"Baseline assignments not found: {args.assignments}. "
            "Run python -m scripts.run_acoustic_baseline first."
        )

    dataset = load_acoustic_spectrum(args.input)
    assignments = validate_assignment_alignment(
        pd.read_csv(args.assignments),
        dataset.observations,
    )
    dynamics = summarize_state_dynamics(assignments)

    shared_dir = args.results_dir / "shared"
    temporal_dir = shared_dir / "temporal"
    figure_dir = shared_dir / "figures"
    sonification_dir = shared_dir / "sonification"
    temporal_dir.mkdir(parents=True, exist_ok=True)
    figure_dir.mkdir(parents=True, exist_ok=True)

    for name, frame in dynamics.items():
        if name != "ordered_assignments":
            frame.to_csv(
                temporal_dir / f"{name}.csv",
                index=name in {"transition_counts", "transition_probabilities"},
            )

    day_type_pivot = dynamics["state_by_day_type"].pivot(
        index="day_type",
        columns="state",
        values="fraction",
    )
    day_type_pivot.to_csv(temporal_dir / "state_by_day_type_pivot.csv")

    sns.set_theme(style="whitegrid")
    save_heatmap(
        dynamics["transition_probabilities"],
        figure_dir / "state_transition_probability.png",
        "State transition probability (consecutive hours, within deployment)",
        cmap="Blues",
        annotate=True,
    )
    save_heatmap(
        dynamics["state_by_month"].pivot(
            index="month",
            columns="state",
            values="fraction",
        ),
        figure_dir / "state_by_month.png",
        "Fraction of observed hours in each state by month",
    )
    save_heatmap(
        dynamics["state_by_day_type"].pivot(
            index="day_type",
            columns="state",
            values="fraction",
        ),
        figure_dir / "state_by_weekday_weekend.png",
        "State share by weekday and weekend",
    )

    duration = dynamics["run_lengths"]
    fig, axis = plt.subplots(figsize=(9, 5))
    sns.boxplot(data=duration, x="state", y="duration_hours", showfliers=False, ax=axis)
    axis.set(
        xlabel="State ID",
        ylabel="Run length (hours)",
        title="Observed state duration (no runs cross gaps or deployments)",
    )
    fig.tight_layout()
    fig.savefig(figure_dir / "state_duration_by_state.png", dpi=180)
    plt.close(fig)

    profiles = (
        dataset.spectrum.assign(state=assignments["state"].to_numpy())
        .groupby("state")
        .median()
        .sort_index()
    )
    if not args.skip_animation:
        create_heartbeat_animation(
            dataset.spectrum,
            assignments,
            figure_dir / "monthly_acoustic_fingerprint.gif",
        )
    create_poster_snapshot(
        assignments=assignments,
        profiles=profiles,
        state_by_month=dynamics["state_by_month"],
        transition_probabilities=dynamics["transition_probabilities"],
        output_path=figure_dir / "poster_research_snapshot.png",
    )

    if not args.skip_sonification:
        sequence, metadata = create_state_tone_sonification(
            assignments,
            sonification_dir / "synthetic_state_tones.wav",
        )
        sequence.to_csv(
            sonification_dir / "synthetic_state_tones_daily_map.csv",
            index=False,
        )
        with (sonification_dir / "metadata.json").open("w", encoding="utf-8") as file:
            json.dump(metadata, file, indent=2)

    transitions = int(dynamics["transition_counts"].to_numpy().sum())
    print(
        f"Generated acoustic-only temporal visuals from {len(assignments)} "
        f"assignments; {transitions} consecutive-hour transitions."
    )
    print(f"Shared outputs saved to {shared_dir}")


if __name__ == "__main__":
    main()
