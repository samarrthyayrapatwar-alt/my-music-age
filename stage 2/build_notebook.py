"""
Builds Stage_2_Data_Pipeline.ipynb from scratch.
Run:  python build_notebook.py
"""
import json
from pathlib import Path


def code_cell(src: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": src.splitlines(keepends=True),
    }


def md_cell(src: str) -> dict:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": src.splitlines(keepends=True),
    }


# ---------------------------------------------------------------------------
# Notebook content
# ---------------------------------------------------------------------------
cells = []

# ----- Title + intro ------------------------------------------------------
cells.append(md_cell("""\
# My Music Age — Stage 2: Data Pipeline

**Goal of this notebook:**
Read a Spotify listening-history file, clean it, and produce a well-structured
DataFrame that later stages (Music Age calculation, visualisation) can use.

**What it demonstrates (course concepts applied):**
- File handling (`open`, `json.load`) — *Module 1, L13*
- Pandas DataFrames, column operations, filtering — *Module 2, L20–22*
- String methods, regex for text cleaning — *Module 1, L4*
- `datetime` extraction for hour / day / month — *Module 2, L21*
- Groupby + aggregation for canonicalisation — *Module 2, L24*

This notebook depends on **`data_pipeline.py`** and **`generate_sample_data.py`**
sitting in the same folder.
"""))

# ----- Section 1: Generate sample data ------------------------------------
cells.append(md_cell("""\
## 1. Generate a sample Spotify export

Real Spotify data takes 1–30 days to arrive after you request it.
We generate a realistic fake file now so the entire pipeline can be
developed and tested. **Swapping in your real export later needs zero
code changes** — both files have the same schema.
"""))

cells.append(code_cell("""\
# Run the generator module as a script.
# This creates StreamingHistory_sample.json in the current folder.
!python3 generate_sample_data.py
"""))

cells.append(md_cell("""\
Peek at the first two records to confirm the format matches what Spotify gives us:
"""))

cells.append(code_cell("""\
import json

with open("StreamingHistory_sample.json", encoding="utf-8") as f:
    sample = json.load(f)

print(f"Total records: {len(sample):,}")
print(f"First record:  {sample[0]}")
print(f"Second record: {sample[1]}")
print(f"Keys:          {list(sample[0].keys())}")
"""))

# ----- Section 2: Load -----------------------------------------------------
cells.append(md_cell("""\
## 2. Load the file into a DataFrame

The `load_listening_history()` function accepts **both** Spotify export
schemas (basic and extended) and our sample file. It returns a DataFrame
with four standardised columns: `end_time`, `artist`, `track`, `ms_played`.
"""))

cells.append(code_cell("""\
from data_pipeline import load_listening_history

raw = load_listening_history("StreamingHistory_sample.json")
print(f"Loaded {len(raw):,} records")
raw.head()
"""))

cells.append(code_cell("""\
# Quick sanity check — what are the column types?
raw.dtypes
"""))

cells.append(code_cell("""\
# And the date range?
print(f"From: {raw['end_time'].min()}")
print(f"To:   {raw['end_time'].max()}")
"""))

# ----- Section 3: Clean ---------------------------------------------------
cells.append(md_cell("""\
## 3. Clean the raw data

The `clean_listening_history()` function performs five operations:

1. **Drop missing rows** — any record without timestamp, artist, track or duration
2. **Normalise strings** — strip whitespace, lowercase the matching keys
3. **Drop skip-throughs** — plays under 30 seconds (default) are usually accidental
4. **Drop exact duplicates** — Spotify sometimes includes them across re-exports
5. **Canonicalise display names** — so "taylor swift" and "Taylor Swift" merge to the common form
6. **Extract derived time columns** — `hour`, `day_of_week`, `month`, `year`, `minutes_played`

It also adds two *key* columns (`artist_key`, `track_key`) that we'll use
to merge with the Kaggle catalogue in Stage 3.
"""))

cells.append(code_cell("""\
from data_pipeline import clean_listening_history

clean = clean_listening_history(raw)
print(f"\\nFinal shape: {clean.shape}")
clean.head()
"""))

cells.append(code_cell("""\
# All the columns we now have, with their purposes:
for col, dtype in zip(clean.columns, clean.dtypes):
    print(f"  {col:15s}  {str(dtype)}")
"""))

# ----- Section 4: Summary -------------------------------------------------
cells.append(md_cell("""\
## 4. Summarise the listening history

The `summarise_listening()` helper returns a dict of headline stats. These
same numbers will feed the "hero banner" of the final report.
"""))

cells.append(code_cell("""\
from data_pipeline import summarise_listening

summary = summarise_listening(clean)
for k, v in summary.items():
    print(f"  {k:15s}  {v}")
"""))

# ----- Section 5: Exploratory checks --------------------------------------
cells.append(md_cell("""\
## 5. Quick exploratory checks

Let's verify the data "feels right" before moving to Stage 3. These
are not part of the final report — just confidence checks.
"""))

cells.append(md_cell("""\
### 5.1  Top 10 artists by play count
"""))

cells.append(code_cell("""\
top_artists = (
    clean.groupby("artist")
         .size()
         .sort_values(ascending=False)
         .head(10)
)
top_artists
"""))

cells.append(md_cell("""\
### 5.2  Top 10 tracks by total listening time
"""))

cells.append(code_cell("""\
top_tracks = (
    clean.groupby(["artist", "track"])["minutes_played"]
         .sum()
         .sort_values(ascending=False)
         .head(10)
         .round(1)
)
top_tracks
"""))

cells.append(md_cell("""\
### 5.3  Listening by hour of day

A realistic listening pattern should peak in the evenings. If our
sample data is well-simulated, we should see that shape here.
"""))

cells.append(code_cell("""\
hourly = (
    clean.groupby("hour")["minutes_played"]
         .sum()
         .round(1)
)
print(hourly)
"""))

cells.append(md_cell("""\
### 5.4  Listening by day of week
"""))

cells.append(code_cell("""\
# Order the days properly (default alphabetical order is wrong)
day_order = ["Monday", "Tuesday", "Wednesday", "Thursday",
             "Friday", "Saturday", "Sunday"]

daily = (
    clean.groupby("day_of_week")["minutes_played"]
         .sum()
         .reindex(day_order)
         .round(1)
)
print(daily)
"""))

# ----- Section 6: Next steps ----------------------------------------------
cells.append(md_cell("""\
## 6. Next step — Stage 3

The `clean` DataFrame is now ready to be joined with a Kaggle Spotify
catalogue (1.2M+ tracks with release years) so we can calculate **Music Age**.

That's Stage 3. Nothing in Stage 3 needs to know how Stage 2 produced its
DataFrame — the only contract between the two is the column set:
`end_time, artist, track, ms_played, artist_key, track_key, hour, day_of_week, month, year, minutes_played`.
"""))

# ---------------------------------------------------------------------------
# Assemble notebook
# ---------------------------------------------------------------------------
notebook = {
    "cells": cells,
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        },
        "language_info": {
            "name": "python",
            "version": "3.10",
        },
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

out = Path("Stage_2_Data_Pipeline.ipynb")
out.write_text(json.dumps(notebook, indent=1), encoding="utf-8")
print(f"Wrote {out} ({out.stat().st_size:,} bytes, {len(cells)} cells)")
