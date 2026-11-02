from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.clustering import evaluate_kmeans_grid, fit_pca_90
from src.data_loading import load_acoustic_spectrum
from src.features import build_interpretable_acoustic_features
from src.poster_visuals import create_poster_snapshot, create_state_tone_sonification
from src.preprocessing import standardize_acoustic_spectrum
from src.rhythm import contiguous_segments, daily_acoustic_frame, discover_motifs
from src.temporal import summarize_state_dynamics


def test_loader_pivots_and_sorts_spectrum(tmp_path):
    source = tmp_path / "acoustic.csv"
    pd.DataFrame(
        {
            "deployment": ["SB01_01"] * 4,
            "time": [
                "2020-01-01T01:00:00Z",
                "2020-01-01T01:00:00Z",
                "2020-01-01T00:00:00Z",
                "2020-01-01T00:00:00Z",
            ],
            "frequency": [20, 10, 20, 10],
            "sound_pressure_levels": [4, 3, 2, 1],
            "source_file": ["unused"] * 4,
        }
    ).to_csv(source, index=False)

    result = load_acoustic_spectrum(source)

    assert result.frequencies == (10.0, 20.0)
    assert result.observations["time"].is_monotonic_increasing
    assert result.spectrum.columns.tolist() == ["sound_10Hz", "sound_20Hz"]
    assert result.spectrum.to_numpy().tolist() == [[1, 2], [3, 4]]


def test_loader_rejects_duplicate_timestamp_frequency(tmp_path):
    source = tmp_path / "duplicate.csv"
    pd.DataFrame(
        {
            "deployment": ["SB01_01"] * 2,
            "time": ["2020-01-01T00:00:00Z"] * 2,
            "frequency": [10, 10],
            "sound_pressure_levels": [1, 2],
        }
    ).to_csv(source, index=False)

    with pytest.raises(ValueError, match="duplicate keys"):
        load_acoustic_spectrum(source)


def test_standardization_and_pca_retain_target_variance():
    spectrum = pd.DataFrame(
        np.random.default_rng(42).normal(size=(80, 5)),
        columns=[f"sound_{i}Hz" for i in range(5)],
    )

    standardized, _ = standardize_acoustic_spectrum(spectrum)
    _, scores, variance = fit_pca_90(standardized)

    assert np.allclose(standardized.mean(axis=0), 0, atol=1e-12)
    assert variance.iloc[scores.shape[1] - 1]["cumulative_explained_variance"] >= 0.90
    assert scores.shape == (80, scores.shape[1])


def test_kmeans_grid_records_seed_stability():
    rng = np.random.default_rng(12)
    representation = np.vstack(
        [
            rng.normal(loc=-3, scale=0.25, size=(40, 3)),
            rng.normal(loc=3, scale=0.25, size=(40, 3)),
        ]
    )

    runs, sizes, models, stability = evaluate_kmeans_grid(
        representation,
        cluster_counts=(2, 3),
        seeds=(1, 2),
        n_init=2,
        silhouette_sample_size=60,
    )

    assert len(runs) == 4
    assert len(sizes) == 10
    assert len(models) == 4
    assert len(stability) == 2
    assert runs["silhouette_sampled"].between(-1, 1).all()
    assert stability["adjusted_rand_index"].between(-1, 1).all()


def test_interpretable_features_use_documented_frequency_ranges():
    spectrum = pd.DataFrame(
        [[10.0, 20.0, 30.0, 40.0, 50.0]],
        columns=[
            "sound_100Hz",
            "sound_250Hz",
            "sound_500Hz",
            "sound_2000Hz",
            "sound_4000Hz",
        ],
    )

    features = build_interpretable_acoustic_features(spectrum)

    assert features.loc[0, "low_mean_level_le_250hz"] == 15
    assert features.loc[0, "mid_mean_level_250_2000hz"] == 35
    assert features.loc[0, "high_mean_level_gt_2000hz"] == 50
    assert features.loc[0, "broadband_mean_level"] == 30
    assert 0 <= features.loc[0, "normalized_spectral_entropy"] <= 1


def test_temporal_transitions_respect_gaps_and_deployment_boundaries():
    assignments = pd.DataFrame(
        {
            "time": [
                "2020-01-01T00:00:00Z",
                "2020-01-01T01:00:00Z",
                "2020-01-01T03:00:00Z",
                "2020-01-01T03:00:00Z",
                "2020-01-01T04:00:00Z",
            ],
            "deployment": ["SB01_01", "SB01_01", "SB01_01", "SB01_02", "SB01_02"],
            "state": [0, 1, 1, 0, 1],
        }
    )

    result = summarize_state_dynamics(assignments)

    assert result["transition_counts"].to_numpy().sum() == 2
    assert result["transition_counts"].loc[0, 1] == 2
    assert result["transition_counts"].loc[1, 1] == 0
    assert result["run_lengths"]["observations"].sum() == len(assignments)


def test_state_tone_sonification_is_labeled_synthetic(tmp_path):
    assignments = pd.DataFrame(
        {
            "time": pd.date_range("2020-01-01", periods=48, freq="h", tz="UTC"),
            "state": [0] * 24 + [1] * 24,
        }
    )
    output = tmp_path / "synthetic.wav"

    daily, metadata = create_state_tone_sonification(
        assignments,
        output,
        days=2,
        sample_rate=8000,
        seconds_per_day=0.05,
    )

    assert output.is_file()
    assert len(daily) == 2
    assert metadata["days_sonified"] == 2
    assert "not a recording" in metadata["interpretation"]


def test_poster_snapshot_writes_weekly_state_share_plot(tmp_path):
    assignments = pd.DataFrame(
        {
            "time": pd.date_range("2020-01-01", periods=48, freq="h", tz="UTC"),
            "state": [0] * 24 + [1] * 24,
        }
    )
    profiles = pd.DataFrame(
        [[10.0, 20.0], [15.0, 25.0]],
        index=pd.Index([0, 1], name="state"),
        columns=["sound_100Hz", "sound_1000Hz"],
    )
    state_by_month = pd.DataFrame(
        {
            "month": ["2020-01", "2020-01"],
            "state": [0, 1],
            "fraction": [0.5, 0.5],
        }
    )
    transition_probabilities = pd.DataFrame(
        [[0.8, 0.2], [0.3, 0.7]],
        index=pd.Index([0, 1], name="from_state"),
        columns=pd.Index([0, 1], name="to_state"),
    )
    output = tmp_path / "poster.png"

    create_poster_snapshot(
        assignments=assignments,
        profiles=profiles,
        state_by_month=state_by_month,
        transition_probabilities=transition_probabilities,
        output_path=output,
    )

    assert output.is_file()
    assert output.stat().st_size > 0


def test_rhythm_tools_do_not_join_across_a_gap_or_deployment():
    hourly = pd.DataFrame(
        {
            "time": pd.to_datetime(
                ["2020-01-01T00:00Z", "2020-01-01T01:00Z", "2020-01-02T00:00Z", "2020-01-02T01:00Z"], utc=True
            ),
            "deployment": ["SB01_01", "SB01_01", "SB01_02", "SB01_02"],
        }
    )
    for index, column in enumerate([
        "low_mean_level_le_250hz", "mid_mean_level_250_2000hz", "high_mean_level_gt_2000hz",
        "broadband_mean_level", "spectral_slope_per_log10_hz", "normalized_spectral_entropy",
    ]):
        hourly[column] = float(index)
    hourly["segment_id"] = contiguous_segments(hourly)
    assert hourly["segment_id"].nunique() == 2
    daily = daily_acoustic_frame(hourly)
    assert daily["acoustic_hours"].tolist() == [2, 2]
    assert discover_motifs(daily, window_days=2).empty
