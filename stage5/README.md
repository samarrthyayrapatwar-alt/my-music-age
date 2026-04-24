# My Music Age — Stage 4: The Wrapped Poster

This stage turns the numbers from Stages 2 and 3 into a single,
shareable Spotify Wrapped-style poster.

## Files

| File | Purpose |
|---|---|
| `wrapped_poster.py` | The rendering module. One public function: `render_poster()`. |
| `Stage_4_Wrapped_Poster.ipynb` | Tutorial notebook — Run All to see the poster. |
| `build_notebook.py` | Rebuilds the `.ipynb` |
| `README.md` | This file |

## Course concepts applied

This stage uses **only syllabus-covered tools**:

- `plt.subplots()` with `gridspec_kw` for multi-panel layout — Module 3, L26
- `ax.barh()` — horizontal bar chart, Module 3, L26
- `ax.text()` — text annotations, Module 3
- `sns.heatmap()` with `sns.dark_palette()` — Module 3, L27 (Statistical Visualization with Seaborn)
- `plt.style.use('dark_background')` — built-in matplotlib style
- Pandas `groupby` + `unstack` for heatmap data prep — Module 2, L24

No external libraries beyond matplotlib and seaborn.

## Setup in your Codespace

Stage 4 depends on Stage 2 + Stage 3. Copy the required modules:

```bash
cp stage2/data_pipeline.py stage4/
cp stage2/StreamingHistory_sample.json stage4/
cp stage3/music_age.py stage4/
ln -s ../catalogue stage4/catalogue
```

Then open `stage4/Stage_4_Wrapped_Poster.ipynb` and Run All.

## What you'll see

A 2:3 portrait-orientation PNG titled `my_music_age_poster.png`
saved to this folder. It has six panels:

1. **Header** — the headline Music Age in huge green type, plus the era profile label
2. **Sub-ages** — weighted vs library age side-by-side
3. **Eras You Live In** — bar chart of decade share, dominant decade in green
4. **Top Track Per Era** — newest to oldest decade, one track each
5. **When You Listen** — day × hour heatmap (`sns.heatmap`)
6. **Footer** — plays / tracks / hours summary

## Retuning the look

Every colour choice is a constant at the top of `wrapped_poster.py`:

```python
SPOTIFY_GREEN = "#1DB954"
SPOTIFY_GRAY  = "#535353"
TEXT_COLOR    = "#F0F0F0"
MUTED_COLOR   = "#A7A7A7"
BG_COLOR      = "#121212"
```

Edit those values to switch palettes. E.g. for purple: change
`SPOTIFY_GREEN` to `"#8B5CF6"`.
