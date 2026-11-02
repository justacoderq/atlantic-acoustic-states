from __future__ import annotations

from pathlib import Path

import matplotlib

# This module is imported directly by tests and notebook users, not only by
# scripts that already select a backend.  A non-interactive backend keeps image
# creation reproducible on headless machines.
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.io import wavfile


def create_heartbeat_animation(
    spectrum: pd.DataFrame,
    assignments: pd.DataFrame,
    output_path: str | Path,
) -> None:
    data = spectrum.copy()
    data["time"] = pd.to_datetime(assignments["time"], utc=True).reset_index(drop=True)
    data["state"] = assignments["state"].to_numpy()
    data["month"] = data["time"].dt.strftime("%Y-%m")
    bands = [
        float(column.removeprefix("sound_").removesuffix("Hz"))
        for column in spectrum.columns
    ]
    monthly = (
        data.groupby(["month", "state"], sort=True)[spectrum.columns]
        .median()
        .reset_index()
    )
    months = sorted(monthly["month"].unique())
    states = sorted(data["state"].unique())
    low, high = float(spectrum.min().min()), float(spectrum.max().max())
    fig, ax = plt.subplots(figsize=(10, 5))

    def update(index: int) -> list[object]:
        ax.clear()
        month = months[index]
        subset = monthly.loc[monthly["month"].eq(month)]
        for state in states:
            row = subset.loc[subset["state"].eq(state)]
            if not row.empty:
                ax.plot(
                    bands,
                    row.iloc[0][spectrum.columns].to_numpy(dtype=float),
                    marker=".",
                    label=f"State {int(state)}",
                )
        ax.set_xscale("log")
        ax.set_xticks(
            [13, 20, 50, 100, 250, 500, 1000, 2000, 5000, 10000, 20000],
            labels=["13", "20", "50", "100", "250", "500", "1k", "2k", "5k", "10k", "20k"],
        )
        ax.set_ylim(low - 1, high + 1)
        ax.set(
            xlabel="Frequency (Hz, log scale)",
            ylabel="Median observed sound level (source units)",
            title=f"Observed monthly acoustic fingerprints: {month}",
        )
        ax.legend(loc="best")
        return list(ax.lines)

    animation = FuncAnimation(fig, update, frames=len(months), interval=350, blit=False)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    animation.save(output, writer=PillowWriter(fps=3))
    plt.close(fig)


def create_state_tone_sonification(
    assignments: pd.DataFrame,
    output_path: str | Path,
    *,
    days: int = 30,
    sample_rate: int = 22050,
    seconds_per_day: float = 0.18,
) -> tuple[pd.DataFrame, dict[str, object]]:
    data = assignments.copy()
    data["time"] = pd.to_datetime(data["time"], utc=True)
    data["utc_date"] = data["time"].dt.floor("D")
    daily = (
        data.groupby("utc_date")["state"]
        .agg(lambda values: int(values.mode().iloc[0]))
        .rename("daily_majority_state")
        .reset_index()
    )
    available = daily["utc_date"].sort_values().reset_index(drop=True)
    if available.empty:
        raise ValueError("Cannot sonify empty state assignments.")
    daily["month"] = daily["utc_date"].dt.strftime("%Y-%m")
    month_counts = daily.groupby("month").size()
    month = str(month_counts.sort_values(ascending=False).index[0])
    period = daily.loc[daily["utc_date"].dt.strftime("%Y-%m").eq(month)].head(days)
    if period.empty:
        raise ValueError("Could not select observed daily state values for sonification.")

    state_ids = sorted(daily["daily_majority_state"].unique())
    state_frequencies = {
        int(state): float(330 * 2 ** (index / max(1, len(state_ids) - 1)))
        for index, state in enumerate(state_ids)
    }
    note_samples = max(1, int(sample_rate * seconds_per_day))
    audio = np.zeros(len(period) * note_samples, dtype=np.float64)
    for index, state in enumerate(period["daily_majority_state"].astype(int)):
        start = index * note_samples
        end = start + note_samples
        time_axis = np.arange(note_samples) / sample_rate
        envelope = np.ones(note_samples)
        fade_samples = min(int(sample_rate * 0.01), note_samples // 2)
        if fade_samples:
            fade = np.linspace(0, 1, fade_samples, endpoint=False)
            envelope[:fade_samples] = fade
            envelope[-fade_samples:] = fade[::-1]
        audio[start:end] = 0.35 * envelope * np.sin(
            2 * np.pi * state_frequencies[int(state)] * time_axis
        )
    encoded = np.int16(np.clip(audio, -1, 1) * 32767)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    wavfile.write(output, sample_rate, encoded)
    sequence = period.copy()
    sequence["tone_hz"] = sequence["daily_majority_state"].map(state_frequencies)
    metadata = {
        "selected_month_utc": month,
        "days_sonified": len(sequence),
        "seconds_per_day": seconds_per_day,
        "sample_rate_hz": sample_rate,
        "state_to_synthetic_tone_hz": state_frequencies,
        "interpretation": "Synthetic state-code tones; not a recording or reconstruction of underwater audio.",
        "output_bytes": output.stat().st_size,
    }
    return sequence, metadata


def create_poster_snapshot(
    *,
    assignments: pd.DataFrame,
    profiles: pd.DataFrame,
    state_by_month: pd.DataFrame,
    transition_probabilities: pd.DataFrame,
    output_path: str | Path,
) -> None:
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    data = assignments.copy()
    data["time"] = pd.to_datetime(data["time"], utc=True)
    data["week_start_utc"] = data["time"].dt.floor("D") - pd.to_timedelta(
        data["time"].dt.dayofweek, unit="D"
    )
    weekly_state_share = (
        data.assign(state_1=data["state"].eq(1).astype(float))
        .groupby("week_start_utc", as_index=False)["state_1"]
        .mean()
    )
    axes[0, 0].plot(
        weekly_state_share["week_start_utc"],
        weekly_state_share["state_1"],
        marker=".",
        linewidth=1.2,
    )
    axes[0, 0].set_ylim(0, 1)
    axes[0, 0].set(
        title="Weekly share of observations in state 1",
        xlabel="Time (UTC)",
        ylabel="Fraction of observed hours",
    )

    frequencies = [
        float(column.removeprefix("sound_").removesuffix("Hz"))
        for column in profiles.columns
    ]
    for state, row in profiles.iterrows():
        axes[0, 1].plot(
            frequencies,
            row.to_numpy(dtype=float),
            label=f"State {int(state)}",
        )
    axes[0, 1].set_xscale("log")
    axes[0, 1].set(
        title="Median acoustic profile",
        xlabel="Frequency (Hz, log scale)",
        ylabel="Median level (source units)",
    )
    axes[0, 1].legend()

    month_pivot = state_by_month.pivot(
        index="month", columns="state", values="fraction"
    )
    sns.heatmap(month_pivot, cmap="viridis", vmin=0, vmax=1, ax=axes[1, 0])
    axes[1, 0].set(title="State share by month", xlabel="State ID", ylabel="Month (UTC)")

    sns.heatmap(
        transition_probabilities,
        annot=True,
        fmt=".2f",
        vmin=0,
        vmax=1,
        cmap="Blues",
        ax=axes[1, 1],
    )
    axes[1, 1].set(
        title="Consecutive-hour transition probability",
        xlabel="To state",
        ylabel="From state",
    )
    fig.suptitle("Stellwagen Bank acoustic-state baseline", fontsize=18)
    fig.tight_layout()
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=180)
    plt.close(fig)
