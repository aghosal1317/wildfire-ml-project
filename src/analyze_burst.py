"""
Burst / awareness-onset detection for the wildfire alert-failure project.

Mirrors collect_data.py's naming convention and looks in one folder
(--data-dir, default: the project's data/ folder, i.e. ../data relative to
this script) for:

    <case>_gdelt.csv
    <case>_reddit_submissions.csv
    <case>_reddit_comments.csv
    <case>_<subreddit>_reddit_local.csv

for case in {lahaina, camp_fire}, and runs burst detection on every file it
finds -- same auto-discovery as wildfire_analysis.ipynb, so a file missing
(e.g. camp_fire_gdelt.csv) is reported and skipped rather than erroring out.
Writes a "<name>_burst.csv" next to each source CSV.

If your CSVs sit somewhere other than data/, pass --data-dir explicitly:

    python analyze_burst.py --data-dir path/to/csvs

Setup:
    pip install pandas

Usage:
    python analyze_burst.py                       # all cases, everything found
    python analyze_burst.py --case lahaina
    python analyze_burst.py --freq 30min --z 2.5
    python analyze_burst.py --file some.csv --timestamp-col created_utc  # one-off file, manual mode
"""

import argparse
import glob
import os

import pandas as pd

CASES = ["lahaina", "camp_fire"]

# CSVs live in <project root>/data, next to this script's src/ folder.
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")

# label -> (filename suffix, timestamp column name)
SOURCE_SUFFIXES = {
    "gdelt": ("_gdelt.csv", "seendate"),
    "reddit_submissions": ("_reddit_submissions.csv", "created_utc"),
    "reddit_comments": ("_reddit_comments.csv", "created_utc"),
}


def find_case_files(case, data_dir):
    """label -> (path, timestamp_col) for every CSV that exists for this case."""
    found = {}
    for label, (suffix, ts_col) in SOURCE_SUFFIXES.items():
        path = os.path.join(data_dir, f"{case}{suffix}")
        if os.path.exists(path):
            found[label] = (path, ts_col)
    for path in sorted(glob.glob(os.path.join(data_dir, f"{case}_*_reddit_local.csv"))):
        sub = os.path.basename(path).replace(f"{case}_", "").replace("_reddit_local.csv", "")
        found[f"local_{sub}"] = (path, "created_utc")
    return found


def load_timestamps(csv_path, timestamp_col):
    df = pd.read_csv(csv_path)
    if timestamp_col not in df.columns:
        print(f"    ! '{timestamp_col}' not in {csv_path}; columns: {list(df.columns)}")
        return pd.Series(dtype="datetime64[ns]")
    col = df[timestamp_col]
    # GDELT's 'seendate' looks like 20230809T120000Z; Reddit/PullPush's
    # 'created_utc' is a Unix epoch integer.
    if col.dtype == object and col.astype(str).str.contains("T").any():
        ts = pd.to_datetime(col, format="%Y%m%dT%H%M%SZ", errors="coerce")
    else:
        ts = pd.to_datetime(col, unit="s", errors="coerce")
    return ts.dropna()


def compute_burst(timestamps, freq="h", baseline_window=6, z_threshold=2.0):
    if timestamps.empty:
        return pd.DataFrame(columns=["count", "z_score", "burst"])
    counts = timestamps.dt.floor(freq).value_counts().sort_index()
    counts = counts.asfreq(freq, fill_value=0)
    rolling_mean = counts.rolling(baseline_window, min_periods=1).mean()
    rolling_std = counts.rolling(baseline_window, min_periods=1).std().fillna(0)
    z = (counts - rolling_mean) / rolling_std.replace(0, 1)
    result = pd.DataFrame({"count": counts, "z_score": z})
    result["burst"] = result["z_score"] >= z_threshold
    return result


def analyze_file(csv_path, timestamp_col, freq, baseline_window, z_threshold):
    ts = load_timestamps(csv_path, timestamp_col)
    result = compute_burst(ts, freq, baseline_window, z_threshold)
    out_path = csv_path.rsplit(".csv", 1)[0] + "_burst.csv"
    result.to_csv(out_path)

    if ts.empty:
        print(f"    -> {out_path} written; no valid timestamps to analyze")
        return
    print(f"    {len(ts)} timestamped rows, {ts.min()} to {ts.max()}")
    if result["burst"].any():
        first_burst = result.index[result["burst"]].min()
        print(f"    -> {out_path} written; first burst at {first_burst}")
    else:
        print(f"    -> {out_path} written; no burst >= z={z_threshold} (try a lower --z)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--data-dir", default=DATA_DIR,
                         help="folder containing the CSVs (default: the project's data/ folder)")
    parser.add_argument("--case", choices=CASES + ["all"], default="all")
    parser.add_argument("--freq", default="h", help="pandas offset alias: h, 30min, D, etc.")
    parser.add_argument("--baseline-window", type=int, default=6,
                         help="number of prior buckets used as the rolling baseline")
    parser.add_argument("--z", type=float, default=2.0, help="z-score threshold for a burst")
    parser.add_argument("--file", help="analyze one specific CSV instead of auto-discovery")
    parser.add_argument("--timestamp-col", help="required when using --file")
    args = parser.parse_args()

    if args.file:
        if not args.timestamp_col:
            parser.error("--timestamp-col is required when using --file")
        print(f"{args.file}:")
        analyze_file(args.file, args.timestamp_col, args.freq, args.baseline_window, args.z)
        raise SystemExit

    for case in (CASES if args.case == "all" else [args.case]):
        found = find_case_files(case, args.data_dir)
        print(f"\n=== {case} ===")
        if not found:
            print(f"  (no CSVs found in {os.path.abspath(args.data_dir)} -- "
                  f"run collect_data.py first, or check --data-dir)")
            continue
        for label, (path, ts_col) in found.items():
            print(f"  {label} ({os.path.basename(path)}):")
            analyze_file(path, ts_col, args.freq, args.baseline_window, args.z)