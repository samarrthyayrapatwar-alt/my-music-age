# My Music Age — Stage 3: Enrichment & Music Age

This stage joins the cleaned listening DataFrame (from Stage 2) with a
Kaggle Spotify catalogue to recover release years, then calculates the
user's Music Age, era distribution, and era profile.

## Files in this folder

| File | Purpose |
|---|---|
| `music_age.py` | Core module. Public functions: `load_catalogue`, `enrich_with_catalogue`, `compute_music_age`, `era_distribution`, `top_track_per_decade`, `assign_era_profile`. |
| `Stage_3_Music_Age.ipynb` | Tutorial notebook — walk through cell by cell. |
| `build_notebook.py` | Rebuilds the `.ipynb` from scratch (you shouldn't need this). |
| `build_proxy_catalogue.py` | Builds a tiny mock catalogue for local testing. **You don't need this in the Codespace** — you have the real Kaggle file. |

## Setup in your Codespace

Stage 3 needs three things from your existing Codespace:

1. **Stage 2 module** — `data_pipeline.py`
2. **Listening data** — `StreamingHistory_sample.json` (or your real file)
3. **Kaggle catalogue** — `catalogue/spotify_data.csv` (you already downloaded this)

### Recommended folder structure

After you upload the Stage 3 files, your codespace should look like this:

```
/workspaces/my-music-age/
├── catalogue/
│   └── spotify_data.csv           ← you downloaded this already
├── synopsis/
│   └── My_Music_Age_Synopsis.docx
├── stage2/
│   ├── data_pipeline.py
│   ├── generate_sample_data.py
│   ├── StreamingHistory_sample.json
│   └── Stage_2_Data_Pipeline.ipynb
└── stage3/                        ← new
    ├── music_age.py
    ├── Stage_3_Music_Age.ipynb
    ├── build_notebook.py
    └── README.md
```

### Running Stage 3

The Stage 3 notebook expects `data_pipeline.py`, `StreamingHistory_sample.json`,
and `catalogue/spotify_data.csv` to sit **in the same folder as the notebook**.

**Easiest way — run these two commands in your Codespace terminal once:**

```bash
# Copy Stage 2 dependencies into Stage 3 so the imports work
cp stage2/data_pipeline.py stage3/
cp stage2/StreamingHistory_sample.json stage3/

# Put the catalogue inside stage3/ too (symlink, doesn't duplicate the 80MB file)
ln -s ../catalogue stage3/catalogue
```

After that, open `stage3/Stage_3_Music_Age.ipynb` and Run All.

### Expected output when you Run All

Match rate: **~75–99%** (depends on how mainstream your taste is).
The sample data gets ~99% match because it's deliberately built from
popular tracks.

Music Age numbers will be two values between, roughly, 5 and 40 years.

Era profile will be one of: **Decade Hopper**, **Future Forward**,
**Vintage Soul**, **{Decade} Loyalist**, or **Balanced Listener**.

## How Stage 3 connects to later stages

Stage 3 produces every number Stage 4 (the visual report) needs:

- `age` dict — two Music Age numbers
- `dist` DataFrame — era breakdown
- `profile` string — era label
- `top` DataFrame — top track per decade

Stage 4 just reads these and draws.
