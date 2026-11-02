from __future__ import annotations

import numpy as np
import pandas as pd


def build_interpretable_acoustic_features(spectrum: pd.DataFrame) -> pd.DataFrame:
    """Create exploratory level summaries and spectral-shape features.

    Bands use their center frequencies: low <= 250 Hz, mid > 250 and <= 2000
    Hz, high > 2000 Hz. Entropy treats stored levels as decibel power levels.
    """
    frequencies = np.asarray(
        [
            float(column.removeprefix("sound_").removesuffix("Hz"))
            for column in spectrum.columns
        ],
        dtype=np.float64,
    )
    levels = spectrum.to_numpy(dtype=np.float64, copy=False)
    if levels.ndim != 2 or levels.shape[1] != len(frequencies) or not len(frequencies):
        raise ValueError("Spectrum columns must be frequency-named numeric bands.")
    if not np.isfinite(levels).all() or (frequencies <= 0).any():
        raise ValueError("Spectrum levels must be finite and frequencies positive.")

    low = (frequencies <= 250)
    mid = (frequencies > 250) & (frequencies <= 2000)
    high = frequencies > 2000
    if not low.any() or not mid.any() or not high.any():
        raise ValueError("Spectrum must have bands in the low, mid, and high ranges.")

    centered_levels = levels - levels.max(axis=1, keepdims=True)
    relative_power = np.power(10.0, centered_levels / 10.0)
    probabilities = relative_power / relative_power.sum(axis=1, keepdims=True)
    entropy = -np.sum(probabilities * np.log(probabilities), axis=1)
    normalized_entropy = entropy / np.log(levels.shape[1])
    log_frequency = np.log10(frequencies)
    log_frequency_centered = log_frequency - log_frequency.mean()
    slope = (
        (levels - levels.mean(axis=1, keepdims=True)) @ log_frequency_centered
        / np.square(log_frequency_centered).sum()
    )

    return pd.DataFrame(
        {
            "low_mean_level_le_250hz": levels[:, low].mean(axis=1),
            "mid_mean_level_250_2000hz": levels[:, mid].mean(axis=1),
            "high_mean_level_gt_2000hz": levels[:, high].mean(axis=1),
            "broadband_mean_level": levels.mean(axis=1),
            "spectral_slope_per_log10_hz": slope,
            "normalized_spectral_entropy": normalized_entropy,
        }
    )
