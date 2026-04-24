# My Music Age — Stage 4: The Wrapped Poster

This stage turns all the numbers from Stages 2 and 3 into a single,
shareable Spotify Wrapped-style poster.

## Files

| File | Purpose |
|---|---|
| `wrapped_poster.py` | The rendering module. One public function: `render_poster()`. |
| `Stage_4_Wrapped_Poster.ipynb` | Tutorial notebook — Run All to see the poster. |
| `build_notebook.py` | Rebuilds the `.ipynb` |
| `README.md` | This file |

## Setup in your Codespace

Stage 4 depends on Stage 2 + Stage 3. Copy the required modules and
create the data symlinks:

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

1. **Header** — the headline Music Age in huge green type, plus the
   era profile label
2. **Sub-ages** — weighted vs library age side-by-side
3. **Eras You Live In** — bar chart of decade share, dominant decade in green
4. **Top Track Per Era** — newest to oldest decade, one track each
5. **When You Listen** — day × hour heatmap
6. **Footer** — plays / tracks / hours summary

## Retuning the look

Every colour and font choice is a constant at the top of
`wrapped_poster.py`:

```python
BG_COLOR        = "#121212"    # background
PANEL_COLOR     = "#1E1E1E"    # card backgrounds
ACCENT_COLOR    = "#1DB954"    # highlights (Spotify green)
MUTED_COLOR     = "#535353"    # non-highlighted bars
TEXT_PRIMARY    = "#F0F0F0"
TEXT_SECONDARY  = "#A7A7A7"
```

Edit those six values to switch palettes entirely. E.g. a purple theme:
change `ACCENT_COLOR` to `"#8B5CF6"`. Light mode: swap `BG_COLOR` to
`"#FAFAFA"`, flip text colours to dark.

## Troubleshooting

- **Text looks fuzzy or fonts wrong** — matplotlib is using a fallback
  font. Install DejaVu Sans via `pip install matplotlib` (should ship
  with it by default).
- **Poster is tiny** — the figure auto-sizes in Jupyter. The saved PNG
  is high-res (200 DPI). For even bigger output, bump `POSTER_DPI` at
  the top of `wrapped_poster.py`.
- **Top track text getting cut off** — artist/track names are truncated
  at 28/30 chars. Edit the `if len(...)` lines in `_draw_top_tracks()`
  to change limits.
