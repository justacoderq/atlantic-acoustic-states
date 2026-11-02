"""Build analysis-ready animal presence tables at their native resolutions.

Applies the decisions recorded in docs/ANIMAL_AUDIT.md:
- blue whale is dropped (0 detections in every analyzed day);
- daily species get one row per UTC day, with the day's acoustic-hour count
  and a keep_day flag (at least MIN_DAY_HOURS acoustic hours);
- dolphins and cod stay hourly; cod is flagged as our own binning of
  NOAA's grunt events.

Run from the repository root:
    python scripts/build_animal_tables.py
"""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Data Mining Project"
ANIMALS_CSV = DATA / "Animal sounds" / "animals.csv"
ACOUSTIC_CSV = DATA / "all.csv"
OUT = ROOT / "data" / "processed"

DROP_SPECIES = {"blue_whale"}
MIN_DAY_HOURS = 20


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    animals = pd.read_csv(ANIMALS_CSV)
    animals["time"] = pd.to_datetime(animals["time"], utc=True)
    animals = animals[~animals["animal"].isin(DROP_SPECIES)]

    acoustic = pd.read_csv(ACOUSTIC_CSV, usecols=["time"]).drop_duplicates()
    acoustic_day = pd.to_datetime(acoustic["time"], utc=True).dt.floor("D")
    day_hours = acoustic_day.value_counts().rename("acoustic_hours")

    # Daily products were repeated across every acoustic hour; collapse back
    # to one value per UTC day. A boundary day is covered by two deployments,
    # each assessing only its part of the day, so the day counts as present
    # if either part had a detection.
    daily = animals[animals["source_resolution"] == "daily"].copy()
    daily["date"] = daily["time"].dt.floor("D")
    daily = (
        daily.groupby(["animal", "date"])
        .agg(
            presence=("presence", "max"),
            deployments=("deployment", lambda s: "+".join(sorted(s.unique()))),
        )
        .reset_index()
        .join(day_hours, on="date")
    )
    daily["keep_day"] = daily["acoustic_hours"] >= MIN_DAY_HOURS
    daily["date"] = daily["date"].dt.strftime("%Y-%m-%d")
    daily.to_csv(OUT / "animals_daily.csv", index=False)

    hourly = animals[animals["source_resolution"] != "daily"].copy()
    hourly["derived_binning"] = hourly["source_resolution"] == "detection_interval"
    hourly = hourly[["time", "deployment", "animal", "presence", "derived_binning"]]
    hourly = hourly.sort_values(["animal", "time"])
    hourly.to_csv(OUT / "animals_hourly.csv", index=False)

    kept = daily[daily["keep_day"]]
    print("Daily species (rows = UTC days kept):")
    print(kept.groupby("animal")["presence"].agg(days="size", present="sum").to_string())
    print(f"Dropped days with < {MIN_DAY_HOURS} acoustic hours: "
          f"{sorted(daily.loc[~daily['keep_day'], 'date'].unique())}")
    print("\nHourly species:")
    print(hourly.groupby("animal")["presence"].agg(hours="size", present="sum").to_string())
    print(f"\nWrote {OUT.relative_to(ROOT)}/animals_daily.csv and animals_hourly.csv")


if __name__ == "__main__":
    main()
