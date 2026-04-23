"""
Builds Stage_3_Music_Age.ipynb from scratch.
"""
import json
from pathlib import Path


def code(src): return {
    "cell_type": "code", "execution_count": None, "metadata": {},
    "outputs": [], "source": src.splitlines(keepends=True)}

def md(src):   return {
    "cell_type": "markdown", "metadata": {},
    "source": src.splitlines(keepends=True)}


cells = []

cells.append(md("""\
# My Music Age — Stage 3: Enrichment & Music Age Calculation

**Goal:** Join Stage 2's cleaned listening DataFrame with a Kaggle Spotify
catalogue to recover release years, then calculate the user's Music Age,
era distribution, and era profile.

**Course concepts applied:**
- Pandas `merge()` with left join — *Module 2, L25*
- Column selection with `usecols` (memory efficiency) — *Module 2, L16*
- NumPy weighted mean — *Module 2, L18*
- Pandas `groupby()` with multiple aggregations — *Module 2, L24*
- Integer binning (decades from years) — *Module 2, L21*
- Rule-based classification (era profile) — *Module 1, conditionals*

**Inputs required in this folder:**
- `data_pipeline.py`       (from Stage 2)
- `StreamingHistory_sample.json`  (from Stage 2, or your real Spotify export)
- `catalogue/spotify_data.csv`    (the Kaggle dataset; see Section 1 below)
- `music_age.py`           (the new Stage 3 module)
"""))

# ---- Section 1: Load the catalogue ----
cells.append(md("""\
## 1. Download the Spotify catalogue from Kaggle

We use Kaggle's `amitanshjoshi/spotify-1million-tracks` dataset — 1 million
songs with columns `artist_name`, `track_name`, `year`, and more.
If you haven't downloaded it yet (80 MB), run the cell below once.

The cell is safe to re-run: it only downloads if the file isn't already there.
"""))

cells.append(code("""\
from pathlib import Path

catalogue_csv = Path("catalogue/spotify_data.csv")

if not catalogue_csv.exists():
    print("Catalogue not found locally — downloading from Kaggle…")
    # Kaggle CLI must be authenticated (KAGGLE_API_TOKEN env var set).
    !kaggle datasets download amitanshjoshi/spotify-1million-tracks -p catalogue --unzip
else:
    size_mb = catalogue_csv.stat().st_size / 1_000_000
    print(f"Catalogue already present: {catalogue_csv} ({size_mb:.1f} MB)")
"""))

# ---- Section 2: Load + clean listening data (Stage 2 recap) ----
cells.append(md("""\
## 2. Load and clean the listening data

This is the Stage 2 pipeline in two lines — no new work, just setting up
our input for Stage 3.
"""))

cells.append(code("""\
from data_pipeline import load_listening_history, clean_listening_history

clean = clean_listening_history(load_listening_history("StreamingHistory_sample.json"))
print(f"Cleaned listening data: {clean.shape}")
clean.head(3)
"""))

# ---- Section 3: Load catalogue ----
cells.append(md("""\
## 3. Load the catalogue

The `load_catalogue()` function reads only the 3 columns we need
(`artist_name`, `track_name`, `year`) out of the 20 in the CSV. This
keeps memory usage low — even with 1M rows, the resulting DataFrame
is under 50 MB.

It also de-duplicates the catalogue: if a song appears multiple times
(original + remaster + compilation), we keep the *earliest* release
year, which is almost always the real original.
"""))

cells.append(code("""\
from music_age import load_catalogue

catalogue = load_catalogue("catalogue/spotify_data.csv")
print(f"Catalogue: {catalogue.shape}")
catalogue.head(3)
"""))

cells.append(code("""\
# Sanity-check: the year column should span from about the 1920s to today
print(f"Earliest release year: {catalogue['release_year'].min()}")
print(f"Latest release year:   {catalogue['release_year'].max()}")
print(f"Median:                {int(catalogue['release_year'].median())}")
"""))

# ---- Section 4: Enrich listening data ----
cells.append(md("""\
## 4. Enrich listening data with release years

This is the core merge: for each play in the listening history, look up
the track in the catalogue and attach its release year.

We use a **left join** so we don't lose any listening rows even if a
track isn't found. Tracks without a release year will just be excluded
from Music Age calculations but remain visible for other analyses.

The `stats` dict tells us how good the match rate was. Aim for > 75%;
> 90% means the catalogue has great coverage of your taste.
"""))

cells.append(code("""\
from music_age import enrich_with_catalogue

enriched, stats = enrich_with_catalogue(clean, "catalogue/spotify_data.csv")

print("Match rate statistics:")
for k, v in stats.items():
    print(f"  {k:20s} {v}")
"""))

cells.append(code("""\
# What do rows look like now? Note the new 'release_year' column.
enriched.head(3)
"""))

cells.append(code("""\
# Which tracks did NOT match the catalogue? These are excluded from Music Age.
unmatched = (enriched[enriched["release_year"].isna()]
             .groupby(["artist", "track"])
             .size()
             .sort_values(ascending=False)
             .head(10))
print("Tracks not found in catalogue (top 10 by play count):")
print(unmatched if len(unmatched) else "  None — all tracks matched!")
"""))

# ---- Section 5: Music Age ----
cells.append(md("""\
## 5. Compute Music Age

This is the headline number. We compute two versions:

| Metric              | What it measures |
|---------------------|------------------|
| **Weighted**        | How old is the music you ACTUALLY LISTEN TO? Each play counts; heavy-rotation songs dominate. |
| **Library**         | How old is your TASTE? Each unique track counts once; breadth matters more than repetition. |

If the two numbers are close, your listening habits match your library.
If *Weighted* is much lower than *Library*, you own a lot of oldies but
mostly play new stuff. And vice-versa.
"""))

cells.append(code("""\
from music_age import compute_music_age

age = compute_music_age(enriched)
for k, v in age.items():
    print(f"  {k:25s} {v}")
"""))

cells.append(code("""\
# Big-number display, the way the final report will show it
print()
print(f"  🎧  Your Music Age (weighted): {age['music_age_weighted']} years")
print(f"  📚  Your Music Age (library):  {age['music_age_library']} years")
print()
print(f"     — based on {age['usable_plays']:,} matched plays")
print(f"        across {age['usable_tracks']} unique tracks.")
"""))

# ---- Section 6: Era distribution ----
cells.append(md("""\
## 6. Era distribution — which decade dominates?

Group every matched play by the decade of its release year, then see
where the listening time piles up. This is what becomes the bar chart
in the final report.
"""))

cells.append(code("""\
from music_age import era_distribution

dist = era_distribution(enriched)
dist
"""))

cells.append(code("""\
# Eyeball the distribution as text bars — the actual chart will be
# built in Stage 4. This is just a sanity check.
for _, row in dist.iterrows():
    bar = "█" * int(row["pct_of_total"])
    print(f"  {row['decade']}  {bar} {row['pct_of_total']}%")
"""))

# ---- Section 7: Era profile ----
cells.append(md("""\
## 7. Assign an era profile label

A single descriptive string that summarises the user's era distribution.
Current rules (in `music_age.py`):

- **`{Decade} Loyalist`** — if one decade exceeds 50%
- **Decade Hopper**       — if 4+ decades each exceed 10%
- **Future Forward**      — if 2010s + 2020s combined exceed 60%
- **Vintage Soul**        — if 1960s + 1970s + 1980s combined exceed 60%
- **Balanced Listener**   — anything else

This is a deliberately simple rule-based classifier: *descriptive*,
not predictive. No ML needed.
"""))

cells.append(code("""\
from music_age import assign_era_profile

profile = assign_era_profile(dist)
print(f"  Era Profile: {profile}")
"""))

# ---- Section 8: Top track per decade ----
cells.append(md("""\
## 8. Top track per decade

For each decade, what did the user listen to the most? This gives
"your most-played 70s song is…" type content for the final report.
"""))

cells.append(code("""\
from music_age import top_track_per_decade

top = top_track_per_decade(enriched)
top
"""))

# ---- Section 9: Next step ----
cells.append(md("""\
## 9. Next step — Stage 4

Stage 3 produces every number the final report needs:

- ✅ Music Age (weighted + library)
- ✅ Era distribution table
- ✅ Era profile label
- ✅ Top track per decade
- ✅ Match-rate stats (for transparency)

Stage 4 is the **visual hero** — a single-page matplotlib poster in
a Spotify-inspired dark theme that brings all of this together. Then
Stage 5 wraps everything in an ipywidgets interface.
"""))

notebook = {
    "cells": cells,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.10"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

out = Path("Stage_3_Music_Age.ipynb")
out.write_text(json.dumps(notebook, indent=1), encoding="utf-8")
print(f"Wrote {out} ({out.stat().st_size:,} bytes, {len(cells)} cells)")
