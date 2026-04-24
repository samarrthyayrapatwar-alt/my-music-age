"""
data_pipeline.py
----------------
Stage 2 of the "My Music Age" project: loading and cleaning Spotify
listening-history files.

Exposes three public functions:
    load_listening_history(path) -> pd.DataFrame
    clean_listening_history(df, skip_threshold_ms=30_000) -> pd.DataFrame
    summarise_listening(df) -> dict

These work identically on:
  - Our generated sample file (stage2/StreamingHistory_sample.json)
  - Spotify's real Account Privacy export (StreamingHistory_music_N.json)
  - Spotify's real Extended Streaming History (endsong_N.json) —
    see `load_listening_history` for the compatibility shim.

Nothing in later stages should need to know which source the data came from.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Union

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# PUBLIC API
# ---------------------------------------------------------------------------

def load_listening_history(path: Union[str, Path]) -> pd.DataFrame:
    """
    Read a Spotify listening-history JSON file into a DataFrame.

    Accepts either schema:
      1. Account Privacy export (basic):
           endTime, artistName, trackName, msPlayed
      2. Extended Streaming History:
           ts, master_metadata_album_artist_name,
           master_metadata_track_name, ms_played, ...
      3. Our generated sample file (same as #1)

    Returns a standardised DataFrame with columns:
        end_time   (datetime64)
        artist     (str, raw — not yet cleaned)
        track      (str, raw — not yet cleaned)
        ms_played  (int)

    Raises:
        FileNotFoundError, ValueError (on malformed input)
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"No such file: {path}")

    try:
        with path.open("r", encoding="utf-8") as f:
            records = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"{path.name} is not valid JSON: {e}") from e

    if not isinstance(records, list) or not records:
        raise ValueError(
            f"{path.name} does not contain a non-empty list of plays"
        )

    # Detect schema by looking at keys of the first record
    first = records[0]
    if "endTime" in first and "artistName" in first:
        # Basic export OR our sample file
        df = pd.DataFrame(records)
        df = df.rename(columns={
            "endTime":    "end_time",
            "artistName": "artist",
            "trackName":  "track",
            "msPlayed":   "ms_played",
        })
    elif "ts" in first and "master_metadata_track_name" in first:
        # Extended streaming history
        df = pd.DataFrame(records)
        df = df.rename(columns={
            "ts":                                  "end_time",
            "master_metadata_album_artist_name":   "artist",
            "master_metadata_track_name":          "track",
            "ms_played":                           "ms_played",
        })
    else:
        raise ValueError(
            f"{path.name} doesn't look like a Spotify export. "
            f"First record keys: {list(first.keys())}"
        )

    # Keep only the columns we care about, in the order we want
    df = df[["end_time", "artist", "track", "ms_played"]]

    # Parse timestamps. Spotify uses either naive or UTC ISO strings;
    # pandas handles both.
    df["end_time"] = pd.to_datetime(df["end_time"], errors="coerce", utc=False)

    # Ensure msPlayed is a real int (defensive — sometimes comes as str)
    df["ms_played"] = pd.to_numeric(df["ms_played"], errors="coerce")

    return df


def clean_listening_history(
    df: pd.DataFrame,
    skip_threshold_ms: int = 30_000,
) -> pd.DataFrame:
    """
    Clean a raw listening DataFrame.

    Operations (in order, each explained inline):
      1. Drop rows with missing critical fields.
      2. Strip whitespace and normalise case in artist/track strings,
         saving both the display version and a matching-key version.
      3. Drop "skip" plays shorter than skip_threshold_ms (default 30s) —
         these are usually accidental clicks, not real listens.
      4. Drop exact duplicates that can appear when Spotify re-exports.
      5. Extract derived time columns for later analysis.

    Adds columns:
        artist_key   lowercase + stripped — for merging with catalogue
        track_key    lowercase + stripped — for merging with catalogue
        hour         0–23
        day_of_week  'Monday' ... 'Sunday'
        month        1–12
        year         4-digit
        minutes_played  float, for convenient aggregations

    Returns a new DataFrame (does not mutate the input).
    """
    df = df.copy()
    n_before = len(df)

    # --- 1. Drop critical nulls -------------------------------------------
    df = df.dropna(subset=["end_time", "artist", "track", "ms_played"])

    # --- 2. Normalise strings ---------------------------------------------
    # We keep the original (trimmed) strings for display, but build
    # *_key columns for robust matching in the next stage.
    df["artist"] = df["artist"].astype(str).str.strip()
    df["track"]  = df["track"].astype(str).str.strip()

    df["artist_key"] = df["artist"].str.lower()
    df["track_key"]  = df["track"].str.lower()

    # Further normalise the keys: collapse internal whitespace so
    # "The  Weeknd" and "The Weeknd" match.
    # Using split() + " ".join() — simple Module 1, L4 string method:
    # split with no args splits on any whitespace and drops empties,
    # then we glue the words back with single spaces.
    df["artist_key"] = df["artist_key"].apply(lambda s: " ".join(s.split()))
    df["track_key"]  = df["track_key"].apply(lambda s: " ".join(s.split()))

    # --- 3. Drop skip-throughs --------------------------------------------
    df = df[df["ms_played"] >= skip_threshold_ms]

    # --- 4. Drop exact duplicates -----------------------------------------
    # An "exact duplicate" = same timestamp + same artist + same track.
    df = df.drop_duplicates(subset=["end_time", "artist_key", "track_key"])

    # --- 4b. Canonicalise display spelling --------------------------------
    # The raw data can contain "Taylor Swift" and "taylor swift" for the
    # same artist. We want the report to show one consistent form.
    # Policy: for each *_key, pick the display form that occurs most often.
    def _most_common(s):
        return s.mode().iat[0] if not s.mode().empty else s.iloc[0]

    canonical_artist = df.groupby("artist_key")["artist"].transform(_most_common)
    canonical_track  = df.groupby(["artist_key", "track_key"])["track"].transform(_most_common)
    df["artist"] = canonical_artist
    df["track"]  = canonical_track

    # --- 5. Derived time columns ------------------------------------------
    df["hour"]           = df["end_time"].dt.hour
    df["day_of_week"]    = df["end_time"].dt.day_name()
    df["month"]          = df["end_time"].dt.month
    df["year"]           = df["end_time"].dt.year
    df["minutes_played"] = df["ms_played"] / 60_000

    # Reset index for clean downstream use
    df = df.reset_index(drop=True)

    # Small stats report (helpful during development; can be silenced)
    n_after = len(df)
    dropped = n_before - n_after
    pct = (dropped / n_before * 100) if n_before else 0
    print(
        f"  cleaned: {n_before:,} → {n_after:,} rows "
        f"(dropped {dropped:,}, {pct:.1f}%)"
    )

    return df


def summarise_listening(df: pd.DataFrame) -> dict:
    """
    One-liner summary of a cleaned listening DataFrame.
    Returns a dict of key stats, suitable for printing or for feeding
    into the ipywidgets dashboard later.
    """
    if df.empty:
        return {"plays": 0}

    total_minutes = df["minutes_played"].sum()
    # Top artist / track by play count
    top_artist = df["artist"].mode().iat[0] if not df["artist"].mode().empty else None
    top_track  = df["track"].mode().iat[0] if not df["track"].mode().empty else None

    return {
        "plays":          len(df),
        "unique_artists": df["artist_key"].nunique(),
        "unique_tracks":  df.groupby(["artist_key", "track_key"]).ngroups,
        "total_minutes":  round(float(total_minutes), 1),
        "total_hours":    round(float(total_minutes) / 60, 1),
        "date_range":     (df["end_time"].min(), df["end_time"].max()),
        "top_artist":     top_artist,
        "top_track":      top_track,
    }


# ---------------------------------------------------------------------------
# If run as a script: quick smoke test against the sample file
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys

    default = Path(__file__).parent / "StreamingHistory_sample.json"
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else default

    print(f"Loading: {path}")
    raw = load_listening_history(path)
    print(f"Loaded {len(raw):,} raw records")
    print(f"Columns: {list(raw.columns)}")
    print(f"Dtypes:\n{raw.dtypes}")
    print()

    print("Cleaning…")
    clean = clean_listening_history(raw)
    print()

    print("Summary:")
    summary = summarise_listening(clean)
    for k, v in summary.items():
        print(f"  {k:15s} {v}")
