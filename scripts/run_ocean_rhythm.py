"""Run gap-aware rhythm discovery and create presentation-ready outputs.

Usage: python -m scripts.run_ocean_rhythm
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.io import wavfile

from src.data_loading import load_acoustic_spectrum
from src.features import build_interpretable_acoustic_features
from src.rhythm import (FEATURE_COLUMNS, anomaly_scores, contiguous_segments,
                        daily_acoustic_frame, detect_change_points, discover_motifs,
                        join_external_context, periodicity_table)
from src.temporal import summarize_state_dynamics

ROOT = Path(__file__).resolve().parents[1]


def args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Discover recurring acoustic rhythms and interruptions.")
    parser.add_argument("--input", type=Path, default=ROOT / "Data Mining Project" / "all.csv")
    parser.add_argument("--results-dir", type=Path, default=ROOT / "results" / "ocean_rhythm")
    parser.add_argument("--max-lag-days", type=int, default=30)
    return parser.parse_args()


def plot_outputs(hourly, daily, periodicity, changes, motifs, context, results: Path) -> None:
    figures = results / "figures"; figures.mkdir(parents=True, exist_ok=True)
    short = periodicity.loc[periodicity["lag_hours"].le(24 * 14)]
    fig, axes = plt.subplots(2, 3, figsize=(15, 7), sharex=True)
    for axis, feature in zip(axes.flat, FEATURE_COLUMNS):
        values = short.loc[short["feature"].eq(feature)]
        axis.plot(values["lag_hours"] / 24, values["autocorrelation"], linewidth=1)
        axis.axvline(1, color="tab:red", alpha=.4); axis.axvline(7, color="tab:red", alpha=.4)
        axis.set(title=feature.replace("_", " "), xlabel="Lag (days)", ylabel="Autocorrelation")
    fig.suptitle("Acoustic rhythm: gap-aware autocorrelation (red = daily/weekly lags)")
    fig.tight_layout(); fig.savefig(figures / "periodicity_autocorrelation.png", dpi=180); plt.close(fig)

    calendar = daily.pivot_table(index=daily["date"].dt.year, columns=daily["date"].dt.dayofyear, values="combined_unusualness")
    fig, ax = plt.subplots(figsize=(15, 4)); sns.heatmap(calendar, cmap="mako_r", center=0, ax=ax)
    ax.set(title="Calendar of unusual acoustic days", xlabel="Day of year", ylabel="Year")
    fig.tight_layout(); fig.savefig(figures / "unusualness_calendar.png", dpi=180); plt.close(fig)

    fig, ax = plt.subplots(figsize=(15, 5))
    ax.plot(daily["date"], daily["combined_unusualness"], color="0.4", linewidth=.7, label="combined unusualness")
    ax.scatter(changes["date"], changes["change_score"], color="tab:red", s=20, label="change points")
    ax.set(title="Abrupt acoustic changes and daily unusualness", xlabel="Date (UTC)", ylabel="Score"); ax.legend()
    fig.tight_layout(); fig.savefig(figures / "change_points_and_anomalies.png", dpi=180); plt.close(fig)

    fig, axes = plt.subplots(min(5, len(motifs)), 1, figsize=(12, max(3, len(motifs) * 2.1)), sharex=True)
    axes = np.atleast_1d(axes)
    for axis, (_, motif) in zip(axes, motifs.head(5).iterrows()):
        for start, label in [(motif["first_start_utc"], "first"), (motif["second_start_utc"], "repeat")]:
            chunk = daily.loc[daily["date"].between(start, start + pd.Timedelta(days=int(motif["window_days"]) - 1))]
            axis.plot(range(len(chunk)), chunk["broadband_mean_level"], marker=".", label=label)
        axis.set(title=f"Motif {int(motif['motif_rank'])}: {motif['distance']:.2f} standardized distance", ylabel="Broadband level")
        axis.legend()
    if len(motifs): axes[-1].set_xlabel("Day within motif window")
    fig.tight_layout(); fig.savefig(figures / "repeated_motifs.png", dpi=180); plt.close(fig)

    state_context = context.select_dtypes("number").groupby(context.get("daily_majority_state"))[ [c for c in ["ship_minutes_mean", "WSPD", "WVHT_44098", "low_mean_level_le_250hz", "high_mean_level_gt_2000hz"] if c in context] ].mean()
    if len(state_context):
        fig, ax = plt.subplots(figsize=(10, 4)); sns.heatmap((state_context - state_context.mean()) / state_context.std(), cmap="vlag", center=0, annot=True, fmt=".1f", ax=ax)
        ax.set(title="External context by daily majority acoustic state (z-scored columns)")
        fig.tight_layout(); fig.savefig(figures / "state_external_context.png", dpi=180); plt.close(fig)

    months = sorted(daily["date"].dt.strftime("%Y-%m").unique())
    fig, ax = plt.subplots(figsize=(12, 3.5))
    def update(index):
        ax.clear(); month = months[index]; subset = daily.loc[daily["date"].dt.strftime("%Y-%m").eq(month)]
        ax.bar(subset["date"].dt.day, subset["combined_unusualness"], color=plt.cm.viridis(np.clip((subset["combined_unusualness"] + 2) / 4, 0, 1)))
        ax.set(title=f"Ocean rhythm calendar: {month}", xlabel="Day of month", ylabel="Unusualness", ylim=(daily["combined_unusualness"].min() - .2, daily["combined_unusualness"].max() + .2))
    animation = FuncAnimation(fig, update, frames=len(months), interval=250)
    animation.save(figures / "ocean_rhythm_calendar.gif", writer=PillowWriter(fps=4)); plt.close(fig)


def create_presentation_media(context: pd.DataFrame, assignments: pd.DataFrame | None, results: Path) -> None:
    """Create clearly labeled synthetic audio and a state-dynamics animation."""
    media = results / "media"; media.mkdir(parents=True, exist_ok=True)
    source = context.dropna(subset=["combined_unusualness"]).head(90).copy()
    if source.empty:
        return
    score = source["combined_unusualness"].to_numpy(float)
    normalized = (score - score.min()) / (score.max() - score.min() or 1)
    sample_rate, seconds = 16_000, 0.12
    samples = int(sample_rate * seconds)
    audio = []
    for value in normalized:
        time = np.arange(samples) / sample_rate
        frequency = 220 + 440 * value
        envelope = np.hanning(samples)
        audio.append(0.3 * envelope * np.sin(2 * np.pi * frequency * time))
    wavfile.write(media / "synthetic_rhythm_summary.wav", sample_rate, np.int16(np.concatenate(audio) * 32767))
    (media / "synthetic_rhythm_summary.json").write_text(json.dumps({
        "days_encoded": len(source), "start_date_utc": str(source.iloc[0]["date"]),
        "encoding": "Each observed day is a synthetic sine tone; higher acoustic unusualness maps to higher pitch.",
        "warning": "This is not original underwater audio or an audio reconstruction."
    }, indent=2), encoding="utf-8")
    if assignments is None or assignments.empty:
        return
    states = assignments.copy(); states["time"] = pd.to_datetime(states["time"], utc=True)
    states["month"] = states["time"].dt.strftime("%Y-%m")
    shares = states.groupby(["month", "state"]).size().groupby(level=0).apply(lambda x: x / x.sum()).unstack(fill_value=0)
    fig, axis = plt.subplots(figsize=(10, 5))
    def update(index):
        axis.clear(); row = shares.iloc[index]
        axis.bar(row.index.astype(str), row.values, color=plt.cm.tab10(np.arange(len(row))))
        axis.set(ylim=(0, 1), xlabel="Acoustic state", ylabel="Observed-hour share", title=f"Acoustic state dynamics: {shares.index[index]}")
    animation = FuncAnimation(fig, update, frames=len(shares), interval=300)
    animation.save(media / "state_dynamics.gif", writer=PillowWriter(fps=4)); plt.close(fig)


def write_interactive(context: pd.DataFrame, results: Path) -> None:
    columns = ["date", "combined_unusualness", "acoustic_anomaly_score", "change_score", "daily_majority_state", "ship_minutes_mean", "WSPD", "WVHT_44098"]
    columns += [column for column in context if column.startswith("animal_")]
    payload = context[[column for column in columns if column in context]].copy()
    payload["date"] = payload["date"].astype(str)
    payload = payload.replace({np.nan: None}).to_dict("records")
    destination = results / "interactive"; destination.mkdir(parents=True, exist_ok=True)
    (destination / "timeline_data.json").write_text(json.dumps(payload), encoding="utf-8")
    (destination / "index.html").write_text("""<!doctype html><meta charset=utf-8><title>The Secret Daily Life of the Atlantic Ocean</title>
<style>body{font:16px system-ui;margin:2rem;background:#071b2d;color:#e7f3fb;max-width:1100px}canvas{width:100%;height:270px;background:#0d2a40;border-radius:10px}#card{background:#10364f;padding:1rem;border-radius:10px;margin-top:1rem}small{color:#b9d4e5}</style>
<h1>The Secret Daily Life of the Atlantic Ocean</h1><p>Click a day to inspect an acoustic anomaly score and independently collected context. These are processed sound-level data, not playable raw audio clips.</p><canvas id=c width=1050 height=270></canvas><div id=card>Loading timeline…</div><small>Higher bars = acoustically unusual days. States/anomalies are discovered from acoustic features only; ship, weather, and animal values are interpretive context.</small>
<script>fetch('timeline_data.json').then(r=>r.json()).then(data=>{let c=document.querySelector('#c'),x=c.getContext('2d'),card=document.querySelector('#card');let values=data.map(d=>d.combined_unusualness||0),min=Math.min(...values),max=Math.max(...values);function draw(i){x.clearRect(0,0,c.width,c.height);data.forEach((d,n)=>{let h=20+(d.combined_unusualness-min)/(max-min||1)*220;x.fillStyle=n==i?'#ffd166':'#38b6ff';x.fillRect(n*c.width/data.length,250-h,Math.max(1,c.width/data.length),h)});let d=data[i];card.innerHTML='<b>'+d.date+'</b><br>Acoustic unusualness: '+(d.combined_unusualness??'n/a').toFixed(2)+' · state: '+(d.daily_majority_state??'n/a')+'<br>Ship minutes/hour: '+(d.ship_minutes_mean??'n/a')+' · wind speed: '+(d.WSPD??'n/a')+' · wave height: '+(d.WVHT_44098??'n/a')+'<br>Animal presence values: '+Object.entries(d).filter(([k,v])=>k.startsWith('animal_')).map(([k,v])=>k.replace('animal_','')+'='+v).join(', ')}draw(0);c.onclick=e=>draw(Math.min(data.length-1,Math.floor(e.offsetX/c.clientWidth*data.length)))})</script>""", encoding="utf-8")


def main() -> None:
    options = args(); results = options.results_dir; tables = results / "tables"; tables.mkdir(parents=True, exist_ok=True)
    dataset = load_acoustic_spectrum(options.input)
    hourly = pd.concat([dataset.observations, build_interpretable_acoustic_features(dataset.spectrum)], axis=1)
    hourly["segment_id"] = contiguous_segments(hourly)
    periodicity = periodicity_table(hourly, options.max_lag_days * 24); daily = daily_acoustic_frame(hourly)
    changes = detect_change_points(daily); daily = anomaly_scores(daily, changes); motifs = discover_motifs(daily)
    assignment_path = ROOT / "results" / "cluster_assignments" / "kmeans_selected_assignments.csv"
    assignments = pd.read_csv(assignment_path) if assignment_path.exists() else None
    context, state_external, animal_state = join_external_context(daily, ROOT, assignments)
    for name, frame in {"hourly_features": hourly, "periodicity_autocorrelation": periodicity, "daily_rhythm": daily, "change_points": changes, "motifs": motifs, "daily_context": context, "state_external_context": state_external, "animal_state_context": animal_state}.items(): frame.to_csv(tables / f"{name}.csv", index=False)
    if assignments is not None:
        dynamics = summarize_state_dynamics(assignments)
        dynamics["transition_probabilities"].to_csv(tables / "gap_aware_state_transitions.csv")
    plot_outputs(hourly, daily, periodicity, changes, motifs, context, results); write_interactive(context, results); create_presentation_media(context, assignments, results)
    top = context.nlargest(10, "combined_unusualness")[["date", "combined_unusualness", "ship_minutes_mean", "WSPD", "WVHT_44098"]]
    top_text = top.to_csv(index=False)
    (results / "README.md").write_text("# Ocean rhythm results\n\nRun with `python -m scripts.run_ocean_rhythm`. The tables contain gap-aware periodicity, repeated seven-day motifs, abrupt changes, acoustic-only anomaly scores, and post-hoc external context. Open `interactive/index.html` in a browser after running. It intentionally contains no claimed original audio: this repository provides processed sound-level observations.\n\n## Top unusual days (CSV)\n\n```csv\n" + top_text + "```\n", encoding="utf-8")
    print(f"Wrote ocean-rhythm results to {results}")

if __name__ == "__main__": main()
