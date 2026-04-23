# My Music Age — Stage 2: Data Pipeline

This folder contains everything needed to load and clean a Spotify listening
history, whether it's our generated sample or your real Spotify export.

## Files

| File | What it does |
|---|---|
| `generate_sample_data.py` | Builds a realistic fake Spotify export (`StreamingHistory_sample.json`). Run once — or re-run to reshuffle the data. |
| `data_pipeline.py` | The core module. Exports three functions: `load_listening_history()`, `clean_listening_history()`, and `summarise_listening()`. Import this into any notebook. |
| `Stage_2_Data_Pipeline.ipynb` | The tutorial notebook. Walk through it cell by cell to see the full pipeline in action. |
| `build_notebook.py` | Utility that rebuilds the notebook above from scratch. You shouldn't need to run this unless you want to edit the notebook programmatically. |
| `StreamingHistory_sample.json` | Generated sample data (3,258 plays, 1 year). |

## How to use it

```bash
# one-time setup
python3 generate_sample_data.py

# open the notebook
jupyter lab Stage_2_Data_Pipeline.ipynb
```

In a notebook cell:

```python
from data_pipeline import load_listening_history, clean_listening_history

raw   = load_listening_history("StreamingHistory_sample.json")
clean = clean_listening_history(raw)
clean.head()
```

## When your real Spotify data arrives

1. Place `StreamingHistory_music_0.json` (and any other `_music_N.json` files) in this folder.
2. Run the same two lines, just with your file name.
3. Everything downstream — Music Age, era distribution, the report — works unchanged.

If you have multiple files (Spotify splits long histories), concatenate them first:

```python
import json, pandas as pd
from pathlib import Path
from data_pipeline import clean_listening_history

records = []
for p in sorted(Path(".").glob("StreamingHistory_music_*.json")):
    records.extend(json.load(p.open(encoding="utf-8")))

Path("StreamingHistory_combined.json").write_text(
    json.dumps(records, ensure_ascii=False), encoding="utf-8"
)

# now proceed as usual
raw   = load_listening_history("StreamingHistory_combined.json")
clean = clean_listening_history(raw)
```

## What the cleaned DataFrame contains

After cleaning, you get these columns:

| Column | Type | Description |
|---|---|---|
| `end_time` | datetime64 | When the play ended |
| `artist` | str | Canonical display name (e.g., "Taylor Swift") |
| `track` | str | Canonical display name (e.g., "Anti-Hero") |
| `ms_played` | int | How long the song played, in milliseconds |
| `artist_key` | str | Lowercased, stripped — for merging with catalogue |
| `track_key` | str | Lowercased, stripped — for merging with catalogue |
| `hour` | int | 0–23 |
| `day_of_week` | str | "Monday" … "Sunday" |
| `month` | int | 1–12 |
| `year` | int | 4-digit year |
| `minutes_played` | float | `ms_played / 60000` for convenient aggregations |

## Next stage

Stage 3 joins this DataFrame with a Kaggle Spotify catalogue to recover
release years for every track, then uses those to calculate your Music Age.
