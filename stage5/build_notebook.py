"""
Builds Stage_4_Wrapped_Poster.ipynb (simplified, syllabus-only version).
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
# My Music Age — Stage 4: The Wrapped Poster

**Goal:** Assemble everything from Stages 2 and 3 into a single-page
Spotify Wrapped-style poster — the visual hero of the project.

**Course concepts applied:**
- `plt.subplots()` with `gridspec_kw` for multi-panel layout — *Module 3, L26*
- `ax.barh()` for horizontal bar charts — *Module 3, L26*
- `ax.text()` for annotations — *Module 3*
- `sns.heatmap()` with `sns.dark_palette()` — *Module 3, L27*
- `plt.style.use('dark_background')` — built-in matplotlib style
- Pandas `groupby` + `unstack` for the heatmap data — *Module 2, L24*

This stage uses ONLY syllabus-covered tools. No external libraries
beyond pandas, numpy, matplotlib, and seaborn.

**Inputs in this folder:**
- `data_pipeline.py`              (from Stage 2)
- `music_age.py`                  (from Stage 3)
- `wrapped_poster.py`             (new, this stage)
- `StreamingHistory_sample.json`
- `catalogue/spotify_data.csv`    (symlinked)

**Output:** `my_music_age_poster.png` (saved to this folder and displayed inline)
"""))

# ---- Section 1: Build the full data pipeline ----
cells.append(md("""\
## 1. Run the full data pipeline

Stages 2 + 3 compressed into two cells. Each call is a function we
built and tested in its own stage.
"""))

cells.append(code("""\
# Stage 2: load + clean
from data_pipeline import (
    load_listening_history,
    clean_listening_history,
    summarise_listening,
)

clean = clean_listening_history(load_listening_history("StreamingHistory_sample.json"))
stats = summarise_listening(clean)
print(f"Cleaned: {len(clean):,} plays")
"""))

cells.append(code("""\
# Stage 3: enrich with catalogue + compute Music Age
from music_age import (
    enrich_with_catalogue,
    compute_music_age,
    era_distribution,
    top_track_per_decade,
    assign_era_profile,
)

enriched, match_stats = enrich_with_catalogue(clean, "catalogue/spotify_data.csv")
age     = compute_music_age(enriched)
dist    = era_distribution(enriched)
top     = top_track_per_decade(enriched)
profile = assign_era_profile(dist)

print(f"Match rate: {match_stats['match_rate_plays']}% of plays")
print(f"Music Age (weighted): {age['music_age_weighted']} years")
print(f"Music Age (library):  {age['music_age_library']} years")
print(f"Era Profile: {profile}")
"""))

# ---- Section 2: Render the poster ----
cells.append(md("""\
## 2. Render the poster

`render_poster()` builds a 6-panel matplotlib figure:

| Panel | Tool used |
|-------|-----------|
| Header | `ax.text()` |
| Sub-ages | `ax.text()` |
| Era bars | `ax.barh()` |
| Top tracks | `ax.text()` |
| Heatmap | `sns.heatmap()` |
| Footer | `ax.text()` |

Layout is `plt.subplots(nrows=6, ncols=1, gridspec_kw={'height_ratios': [...]})`
— basic matplotlib (Module 3).
"""))

cells.append(code("""\
from wrapped_poster import render_poster
import matplotlib.pyplot as plt

fig = render_poster(
    age=age,
    era_dist=dist,
    top_per_decade=top,
    listening_df=enriched,
    profile=profile,
    listening_stats=stats,
    out_path="my_music_age_poster.png",
)

plt.show()
print("\\nSaved to my_music_age_poster.png")
"""))

# ---- Section 3: Retuning ----
cells.append(md("""\
## 3. Retuning the visual (optional)

Every colour choice lives at the top of `wrapped_poster.py`. To try
a different palette, edit these and re-render:

```python
SPOTIFY_GREEN = "#1DB954"     # accent (hero number, dominant bar)
SPOTIFY_GRAY  = "#535353"     # non-dominant bars
TEXT_COLOR    = "#F0F0F0"     # primary text
MUTED_COLOR   = "#A7A7A7"     # secondary labels
BG_COLOR      = "#121212"     # poster background
```

For example, change `SPOTIFY_GREEN` to `"#8B5CF6"` for a purple theme.
"""))

# ---- Section 4: Next step ----
cells.append(md("""\
## 4. Next step — Stage 5

Stage 5 wraps everything into a simple `run()` function plus an
`interactive()` prompt. That stage is the user-facing entry point.
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

out = Path("Stage_4_Wrapped_Poster.ipynb")
out.write_text(json.dumps(notebook, indent=1), encoding="utf-8")
print(f"Wrote {out} ({out.stat().st_size:,} bytes, {len(cells)} cells)")
