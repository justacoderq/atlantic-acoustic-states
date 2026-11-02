"""Audit the SanctSound animal NetCDF files against Animal sounds/animals.csv.

Reads every raw/*.nc product, records its metadata, and checks that the
derived CSV reproduces its presence values at the product's native
resolution. Writes per-file and coverage tables to results/tables/.

Run from the repository root:
    python scripts/audit_animals.py
"""

import re
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Data Mining Project"
RAW = DATA / "Animal sounds" / "raw"
ANIMALS_CSV = DATA / "Animal sounds" / "animals.csv"
ACOUSTIC_CSV = DATA / "all.csv"
OUT = ROOT / "results" / "tables"

NAME_RE = re.compile(r"SanctSound_(SB01_\d{2})_([a-z]+?)(?:_(1d|1h))?\.nc$")
GAP_RE = re.compile(
    r"(\d{4}-\d{2}-\d{2}(?: \d{2}:\d{2})?)\s+(?:and|to|-)\s+"
    r"(\d{4}-\d{2}-\d{2}(?: \d{2}:\d{2})?)"
)
HOUR_MS = 3_600_000
DAY_MS = 86_400_000


def ms_to_utc(ms):
    return pd.to_datetime(np.asarray(ms, dtype="int64"), unit="ms", utc=True)


def read_product(path):
    ds = xr.open_dataset(path, engine="h5netcdf", decode_times=False)
    presence_var = next(v for v in ds.data_vars if v.endswith("_presence"))
    df = pd.DataFrame({
        "start": ms_to_utc(ds["start_time"].values),
        "end": ms_to_utc(ds["end_time"].values),
        "presence": ds[presence_var].values.astype(int),
    })
    attrs = dict(ds.attrs)
    ds.close()
    return df, attrs


def parse_gaps(comment):
    """Return (start, end) UTC pairs from a 'Data quality' comment."""
    gaps = []
    for a, b in GAP_RE.findall(comment or ""):
        gaps.append((pd.Timestamp(a, tz="UTC"), pd.Timestamp(b, tz="UTC")))
    return gaps


def audit_file(path, csv_rows, acoustic_hours):
    m = NAME_RE.search(path.name)
    deployment, species, suffix = m.group(1), m.group(2), m.group(3)
    nc, attrs = read_product(path)
    duration = (nc["end"] - nc["start"]).dt.total_seconds()
    row = {
        "file": path.name,
        "deployment": deployment,
        "species_file": species,
        "product": {"1d": "daily", "1h": "hourly", None: "events"}[suffix],
        "nc_records": len(nc),
        "nc_first": nc["start"].min(),
        "nc_last": nc["end"].max(),
        "nc_present": int(nc["presence"].sum()),
        "nc_all_present": bool((nc["presence"] == 1).all()),
        "nc_median_duration_s": float(duration.median()),
        "doi": attrs.get("id", ""),
        "date_created": attrs.get("date_created", ""),
        "quality_comment": attrs.get("comment", ""),
    }

    csv = csv_rows.sort_values("time")
    row["csv_rows"] = len(csv)
    row["csv_resolution"] = csv["source_resolution"].iloc[0] if len(csv) else ""
    row["csv_present_rows"] = int(csv["presence"].sum())
    dep_hours = acoustic_hours.get(deployment, pd.DatetimeIndex([]))
    row["csv_hours_equal_acoustic_hours"] = bool(
        pd.DatetimeIndex(csv["time"]).equals(dep_hours)
    )

    if row["product"] == "daily":
        steps = nc["start"].diff().dropna().dt.total_seconds() * 1000
        row["nc_regular"] = bool((steps == DAY_MS).all() and (duration * 1000 == DAY_MS).all())
        nc_day = nc.set_index(nc["start"].dt.floor("D"))["presence"]
        csv_day = csv["time"].dt.floor("D")
        expected = csv_day.map(nc_day)
        row["csv_unique_days"] = int(csv_day.nunique())
        row["csv_hours_without_nc_day"] = int(expected.isna().sum())
        row["mismatches"] = int((expected.dropna() != csv["presence"][expected.notna()]).sum())
        row["nc_units_not_in_csv"] = int((~nc_day.index.isin(csv_day)).sum())
        per_day = csv.groupby(csv_day)["presence"].nunique()
        row["csv_days_inconsistent"] = int((per_day > 1).sum())
    elif row["product"] == "hourly":
        steps = nc["start"].diff().dropna().dt.total_seconds() * 1000
        row["nc_regular"] = bool((steps == HOUR_MS).all() and (duration * 1000 == HOUR_MS).all())
        nc_hour = nc.set_index("start")["presence"]
        expected = csv["time"].map(nc_hour)
        row["csv_hours_without_nc_day"] = int(expected.isna().sum())
        row["mismatches"] = int((expected.dropna() != csv["presence"][expected.notna()]).sum())
        row["nc_units_not_in_csv"] = int((~nc_hour.index.isin(csv["time"])).sum())
    else:
        # Event list: one record per detected call. Absences are not recorded,
        # so the CSV's zeros were created by binning events onto an hour grid.
        row["nc_regular"] = None
        event_hours = nc.loc[nc["presence"] == 1, "start"].dt.floor("h")
        hours_with_events = pd.DatetimeIndex(event_hours.unique())
        csv_present = pd.DatetimeIndex(csv.loc[csv["presence"] == 1, "time"])
        row["event_hours"] = len(hours_with_events)
        row["mismatches"] = int(len(hours_with_events.symmetric_difference(csv_present)))
        row["nc_units_not_in_csv"] = int((~hours_with_events.isin(csv["time"])).sum())
        row["events_outside_csv_hours"] = int((~event_hours.isin(csv["time"])).sum())
        counts = event_hours.value_counts()
        row["events_per_present_hour_median"] = float(counts.median()) if len(counts) else 0.0
        row["events_per_present_hour_max"] = int(counts.max()) if len(counts) else 0

    gaps = parse_gaps(row["quality_comment"])
    row["quality_gaps"] = len(gaps)
    row["csv_hours_in_quality_gaps"] = int(sum(
        ((csv["time"] + pd.Timedelta(hours=1) > a) & (csv["time"] < b)).sum() for a, b in gaps
    ))
    return row


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    animals = pd.read_csv(ANIMALS_CSV)
    animals["time"] = pd.to_datetime(animals["time"], utc=True)
    acoustic = pd.read_csv(ACOUSTIC_CSV, usecols=["deployment", "time"]).drop_duplicates()
    acoustic["time"] = pd.to_datetime(acoustic["time"], utc=True)
    acoustic_hours = {
        dep: pd.DatetimeIndex(g["time"].sort_values().unique())
        for dep, g in acoustic.groupby("deployment")
    }

    by_file = dict(tuple(animals.groupby("source_file")))
    nc_files = sorted(RAW.glob("*.nc"))
    rows = [
        audit_file(p, by_file.get(p.name, animals.iloc[0:0]), acoustic_hours)
        for p in nc_files
    ]
    files = pd.DataFrame(rows)
    files["species"] = files["file"].map(
        animals.drop_duplicates("source_file").set_index("source_file")["animal"]
    )
    files.to_csv(OUT / "animal_audit_files.csv", index=False)

    csv_only = sorted(set(animals["source_file"]) - {p.name for p in nc_files})

    # Presence summary at native resolution (one count per day for daily
    # products, per hour for dolphins and the hour-binned cod events).
    native = animals.copy()
    daily = native["source_resolution"] == "daily"
    native.loc[daily, "time"] = native.loc[daily, "time"].dt.floor("D")
    native = native.drop_duplicates(["deployment", "animal", "time"])
    coverage = native.pivot_table(
        index="animal", columns="deployment", values="presence", aggfunc="size"
    )
    coverage.to_csv(OUT / "animal_coverage_units.csv")
    summary = native.groupby(["animal", "source_resolution"]).agg(
        deployments=("deployment", "nunique"),
        units=("presence", "size"),
        present_units=("presence", "sum"),
        first=("time", "min"),
        last=("time", "max"),
    )
    summary["present_pct"] = (100 * summary["present_units"] / summary["units"]).round(1)
    summary.to_csv(OUT / "animal_presence_native.csv")

    pd.set_option("display.width", 200)
    print(f"NetCDF files: {len(nc_files)}; CSV source files: {animals['source_file'].nunique()}")
    print(f"CSV files with no NetCDF: {csv_only or 'none'}")
    print("\nPresence at native resolution:")
    print(summary.to_string())
    print("\nCoverage (native units per deployment):")
    print(coverage.fillna(0).astype(int).to_string())
    cols = ["product", "nc_regular", "nc_all_present", "mismatches", "csv_hours_without_nc_day",
            "nc_units_not_in_csv", "csv_hours_equal_acoustic_hours", "csv_days_inconsistent",
            "csv_hours_in_quality_gaps"]
    print("\nCheck totals by product:")
    print(files.groupby("product")[cols[1:]].agg(
        lambda s: s.sum() if s.dtype != object else s.value_counts(dropna=False).to_dict()
    ).to_string())
    print(f"\nWrote {OUT.relative_to(ROOT)}/animal_audit_files.csv, "
          "animal_coverage_units.csv, animal_presence_native.csv")


if __name__ == "__main__":
    main()
