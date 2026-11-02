from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class AcousticDataset:
    observations: pd.DataFrame
    spectrum: pd.DataFrame
    frequencies: tuple[float, ...]
    source_rows: int


def load_acoustic_spectrum(path: str | Path) -> AcousticDataset:
    """Load long-format sound levels as one complete spectrum per UTC hour."""
    data = pd.read_csv(
        path,
        usecols=[
            "deployment",
            "time",
            "frequency",
            "sound_pressure_levels",
        ],
        low_memory=False,
    )
    data["time"] = pd.to_datetime(data["time"], errors="coerce", utc=True)
    data["frequency"] = pd.to_numeric(data["frequency"], errors="coerce")
    data["sound_pressure_levels"] = pd.to_numeric(
        data["sound_pressure_levels"], errors="coerce"
    )
    if data[["deployment", "time", "frequency", "sound_pressure_levels"]].isna().any().any():
        raise ValueError("Acoustic input contains missing or invalid required values.")

    duplicate_keys = data.duplicated(["time", "frequency"], keep=False)
    if duplicate_keys.any():
        examples = data.loc[duplicate_keys, ["time", "frequency"]].head(3)
        raise ValueError(
            "Expected one acoustic value per timestamp and frequency; "
            f"duplicate keys include {examples.to_dict('records')}."
        )

    deployment_counts = data.groupby("time", sort=False)["deployment"].nunique()
    if deployment_counts.ne(1).any():
        raise ValueError("A timestamp is associated with multiple deployments.")

    frequencies = tuple(sorted(data["frequency"].unique().tolist()))
    spectrum = (
        data.pivot(index="time", columns="frequency", values="sound_pressure_levels")
        .reindex(columns=frequencies)
        .sort_index()
    )
    incomplete = spectrum.isna().any(axis=1)
    if incomplete.any():
        raise ValueError(
            f"{int(incomplete.sum())} hourly spectra are incomplete; "
            "resolve them explicitly rather than imputing values silently."
        )

    deployments = (
        data.drop_duplicates("time")
        .set_index("time")["deployment"]
        .reindex(spectrum.index)
        .rename("deployment")
    )
    observations = pd.DataFrame(
        {
            "row_index": range(len(spectrum)),
            "time": spectrum.index,
            "deployment": deployments.to_numpy(),
        }
    )
    spectrum.columns = [f"sound_{frequency:g}Hz" for frequency in frequencies]
    spectrum = spectrum.reset_index(drop=True)
    return AcousticDataset(observations, spectrum, frequencies, len(data))
