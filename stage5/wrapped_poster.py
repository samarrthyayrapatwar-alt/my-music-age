"""
wrapped_poster.py
-----------------
Stage 4 of the "My Music Age" project.

Renders a single-page Spotify Wrapped-style poster summarising the
user's Music Age report.

Built using ONLY syllabus-covered tools:
  - matplotlib subplots, bar charts, text annotations  (Module 3, L26)
  - seaborn histplot                                   (Module 3, L27)
  - matplotlib's built-in 'dark_background' style
  - matplotlib axvline for the mean reference line     (Module 3, L26)

No FancyBboxPatch, no GridSpec, no custom colormaps, no inset_axes,
no heatmap (which isn't in the syllabus) — everything in this file
maps to a session in the course outline.

Public API:
    render_poster(age, era_dist, top_per_decade, listening_df,
                  profile, listening_stats=None, out_path=None) -> Figure
"""

from __future__ import annotations

from pathlib import Path
from typing import Union

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


# ---------------------------------------------------------------------------
# DESIGN CONSTANTS
# ---------------------------------------------------------------------------

# Spotify-inspired palette. Just hex strings.
SPOTIFY_GREEN = "#1DB954"
SPOTIFY_GRAY  = "#535353"
TEXT_COLOR    = "#F0F0F0"
MUTED_COLOR   = "#A7A7A7"
BG_COLOR      = "#121212"

# Poster dimensions: portrait, presentation-friendly
POSTER_W_IN = 8
POSTER_H_IN = 12
POSTER_DPI  = 200


# ---------------------------------------------------------------------------
# PANEL DRAWERS — each fills one axes
# ---------------------------------------------------------------------------

def _clear(ax):
    """Strip ticks, spines and labels — we only want our own text on this axes."""
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_facecolor(BG_COLOR)


def _draw_header(ax, age: dict, profile: str):
    """Top panel: 'MY MUSIC AGE' title + huge hero number + era profile label."""
    _clear(ax)

    # Eyebrow label
    ax.text(0.5, 0.98, "MY MUSIC AGE",
            ha="center", va="top",
            color=MUTED_COLOR, fontsize=12, fontweight="bold",
            transform=ax.transAxes)

    # Hero number (weighted Music Age) — biggest text on the poster
    weighted = age.get("music_age_weighted")
    hero = f"{weighted:.1f}" if weighted is not None else "—"
    ax.text(0.5, 0.55, hero,
            ha="center", va="center",
            color=SPOTIFY_GREEN, fontsize=90, fontweight="bold",
            transform=ax.transAxes)

    ax.text(0.5, 0.22, "YEARS",
            ha="center", va="center",
            color=TEXT_COLOR, fontsize=18, fontweight="bold",
            transform=ax.transAxes)

    ax.text(0.5, 0.05, profile.upper(),
            ha="center", va="center",
            color=TEXT_COLOR, fontsize=16, style="italic",
            transform=ax.transAxes)


def _draw_subages(ax, age: dict):
    """Side-by-side weighted vs library age."""
    _clear(ax)

    # Left side — weighted
    ax.text(0.25, 0.78, "WEIGHTED", ha="center", va="center",
            color=MUTED_COLOR, fontsize=10, fontweight="bold",
            transform=ax.transAxes)
    w = age.get("music_age_weighted")
    ax.text(0.25, 0.45, f"{w:.1f}" if w is not None else "—",
            ha="center", va="center",
            color=TEXT_COLOR, fontsize=30, fontweight="bold",
            transform=ax.transAxes)
    ax.text(0.25, 0.15, "what you play most", ha="center", va="center",
            color=MUTED_COLOR, fontsize=9,
            transform=ax.transAxes)

    # Right side — library
    ax.text(0.75, 0.78, "LIBRARY", ha="center", va="center",
            color=MUTED_COLOR, fontsize=10, fontweight="bold",
            transform=ax.transAxes)
    l = age.get("music_age_library")
    ax.text(0.75, 0.45, f"{l:.1f}" if l is not None else "—",
            ha="center", va="center",
            color=TEXT_COLOR, fontsize=30, fontweight="bold",
            transform=ax.transAxes)
    ax.text(0.75, 0.15, "your whole taste", ha="center", va="center",
            color=MUTED_COLOR, fontsize=9,
            transform=ax.transAxes)


def _draw_era_bars(ax, era_dist: pd.DataFrame):
    """
    Horizontal bar chart of era distribution.
    Uses ax.barh() — basic matplotlib (Module 3, L26).
    Dominant decade is highlighted in green; others muted gray.
    """
    ax.set_facecolor(BG_COLOR)

    # Title
    ax.set_title("ERAS YOU LIVE IN", loc="left", color=MUTED_COLOR,
                 fontsize=11, fontweight="bold", pad=10)

    if era_dist.empty:
        ax.text(0.5, 0.5, "No matched tracks",
                ha="center", va="center",
                color=MUTED_COLOR, fontsize=12, transform=ax.transAxes)
        _clear(ax)
        return

    decades = era_dist["decade"].tolist()
    pcts    = era_dist["pct_of_total"].tolist()
    top_idx = pcts.index(max(pcts))

    # One color per bar; the dominant decade is green, others gray
    colors = [SPOTIFY_GREEN if i == top_idx else SPOTIFY_GRAY
              for i in range(len(decades))]

    # Draw bars — newest at top reads more naturally
    y_pos = list(range(len(decades)))
    ax.barh(y_pos, pcts, color=colors, edgecolor="none")
    ax.invert_yaxis()  # so 1960s is at top, 2020s at bottom — chronological

    # Decade labels on the y-axis
    ax.set_yticks(y_pos)
    ax.set_yticklabels(decades, color=TEXT_COLOR, fontsize=11, fontweight="bold")

    # Hide x-axis but show percentages at the end of each bar
    ax.set_xticks([])
    for i, pct in enumerate(pcts):
        color = TEXT_COLOR if i == top_idx else MUTED_COLOR
        weight = "bold" if i == top_idx else "normal"
        ax.text(pct + max(pcts) * 0.02, i, f"{pct:.1f}%",
                va="center", color=color, fontsize=10, fontweight=weight)

    # Remove all spines for a clean look
    for spine in ax.spines.values():
        spine.set_visible(False)

    # Give right margin so the % labels don't get clipped
    ax.set_xlim(0, max(pcts) * 1.15)


def _draw_top_tracks(ax, top_per_decade: pd.DataFrame):
    """
    List of top tracks per decade. Uses ax.text() repeatedly — simple
    matplotlib text positioning, no fancy widgets.
    """
    _clear(ax)

    ax.set_title("TOP TRACK PER ERA", loc="left", color=MUTED_COLOR,
                 fontsize=11, fontweight="bold", pad=10)

    if top_per_decade.empty:
        ax.text(0.5, 0.5, "No matched tracks",
                ha="center", va="center",
                color=MUTED_COLOR, fontsize=12, transform=ax.transAxes)
        return

    # Sort newest decade at top — reads more naturally
    rows = top_per_decade.sort_values("decade", ascending=False)
    n = len(rows)

    # Equally spaced rows from top to bottom
    top_y = 0.85
    bot_y = 0.05
    if n > 1:
        step = (top_y - bot_y) / (n - 1)
    else:
        step = 0
    for i, (_, r) in enumerate(rows.iterrows()):
        y = top_y - i * step

        # Decade label (left, green accent)
        ax.text(0.04, y, r["decade"],
                ha="left", va="center",
                color=SPOTIFY_GREEN, fontsize=11, fontweight="bold",
                transform=ax.transAxes)

        # Track name (white, bold)
        track = r["track"]
        if len(track) > 26:
            track = track[:24] + "…"
        ax.text(0.20, y, track,
                ha="left", va="center",
                color=TEXT_COLOR, fontsize=11, fontweight="bold",
                transform=ax.transAxes)

        # Artist name (muted, after the track on the same line)
        artist = r["artist"]
        if len(artist) > 22:
            artist = artist[:20] + "…"
        ax.text(0.62, y, f"— {artist}",
                ha="left", va="center",
                color=MUTED_COLOR, fontsize=10,
                transform=ax.transAxes)


def _draw_release_year_distribution(ax, enriched_df: pd.DataFrame):
    """
    Histogram showing the distribution of release years across the user's
    matched plays. The mean of this distribution = the user's mean release
    year, which is what 'Music Age' is computed from.

    Uses sns.histplot() — Module 3, L27 (Statistical Visualization with
    Seaborn: Boxplots, countplots, histplots, distplots).

    A vertical reference line marks the weighted mean release year — the
    line is what connects the visual to the headline Music Age number.
    Vertical line uses ax.axvline() — basic matplotlib, Module 3 L26.
    """
    ax.set_facecolor(BG_COLOR)
    ax.set_title("YOUR LISTENING ACROSS THE YEARS",
                 loc="left", color=MUTED_COLOR,
                 fontsize=11, fontweight="bold", pad=10)

    usable = enriched_df.dropna(subset=["release_year"]).copy()
    if usable.empty:
        ax.text(0.5, 0.5, "No matched tracks",
                ha="center", va="center",
                color=MUTED_COLOR, fontsize=12, transform=ax.transAxes)
        return

    usable["release_year"] = usable["release_year"].astype(int)

    # The weighted mean we used to compute Music Age — drawn as a
    # vertical reference line on top of the distribution.
    weights = usable["ms_played"].to_numpy()
    years_arr = usable["release_year"].to_numpy()
    weighted_mean_year = float((years_arr * weights).sum() / weights.sum())

    # Draw the histogram (each play counts as one observation; no
    # explicit weighting in the bars themselves to keep this simple).
    sns.histplot(
        data=usable,
        x="release_year",
        ax=ax,
        color=SPOTIFY_GREEN,
        edgecolor=BG_COLOR,
        bins=20,
        alpha=0.85,
    )

    # Reference line at the weighted mean
    ax.axvline(
        weighted_mean_year,
        color=TEXT_COLOR,
        linestyle="--",
        linewidth=1.5,
        alpha=0.8,
    )
    ax.text(
        weighted_mean_year, ax.get_ylim()[1] * 0.92,
        f"  mean: {weighted_mean_year:.0f}",
        color=TEXT_COLOR, fontsize=9, fontweight="bold",
        ha="left", va="top",
    )

    # Style: muted axes, no top/right spines
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    for spine in ["left", "bottom"]:
        ax.spines[spine].set_color(MUTED_COLOR)

    ax.tick_params(colors=MUTED_COLOR, labelsize=9, length=0)
    ax.set_xlabel("RELEASE YEAR", color=MUTED_COLOR, fontsize=8, labelpad=6)
    ax.set_ylabel("PLAYS", color=MUTED_COLOR, fontsize=8, labelpad=6)


def _draw_footer(ax, age: dict, listening_stats: dict):
    """Tiny footer with credit + transparency about sample size."""
    _clear(ax)

    plays = age.get("usable_plays", 0)
    tracks = age.get("usable_tracks", 0)
    hours = listening_stats.get("total_minutes", 0) / 60

    ax.text(0.5, 0.7,
            f"Generated from {plays:,} matched plays across {tracks} tracks "
            f"· {hours:,.0f} hours of listening",
            ha="center", va="center",
            color=MUTED_COLOR, fontsize=9, transform=ax.transAxes)
    ax.text(0.5, 0.25,
            "My Music Age · Programming in Python · Vidyashilp University",
            ha="center", va="center",
            color=MUTED_COLOR, fontsize=8, style="italic",
            transform=ax.transAxes)


# ---------------------------------------------------------------------------
# PUBLIC — assemble all panels into one Figure
# ---------------------------------------------------------------------------

def render_poster(
    age: dict,
    era_dist: pd.DataFrame,
    top_per_decade: pd.DataFrame,
    listening_df: pd.DataFrame,
    profile: str,
    listening_stats: dict | None = None,
    out_path: Union[str, Path, None] = None,
):
    """
    Build and return the My Music Age poster as a matplotlib Figure.

    Uses plt.subplots() with 6 rows, 1 column — basic matplotlib layout.
    Each row is one panel of the report.
    """
    if listening_stats is None:
        listening_stats = {"total_minutes": listening_df["minutes_played"].sum()}

    # Apply matplotlib's built-in dark theme — sets sensible defaults
    # (dark background, light text). One line, no custom rcParams hacking.
    plt.style.use("dark_background")

    # 6 rows × 1 column. Row heights are not perfectly equal —
    # we use gridspec_kw to give some panels more vertical space.
    # gridspec_kw is just a parameter to plt.subplots — basic Module 3.
    fig, axes = plt.subplots(
        nrows=6, ncols=1,
        figsize=(POSTER_W_IN, POSTER_H_IN),
        gridspec_kw={
            "height_ratios": [3.0, 1.2, 2.5, 3.0, 2.5, 0.4],
            "hspace": 0.6,
        },
    )
    fig.patch.set_facecolor(BG_COLOR)

    _draw_header(axes[0], age, profile)
    _draw_subages(axes[1], age)
    _draw_era_bars(axes[2], era_dist)
    _draw_top_tracks(axes[3], top_per_decade)
    _draw_release_year_distribution(axes[4], listening_df)
    _draw_footer(axes[5], age, listening_stats)

    # Tighten margins
    fig.subplots_adjust(left=0.10, right=0.92, top=0.97, bottom=0.03)

    if out_path:
        fig.savefig(
            out_path,
            dpi=POSTER_DPI,
            facecolor=BG_COLOR,
            bbox_inches="tight",
            pad_inches=0.2,
        )

    return fig


# ---------------------------------------------------------------------------
# Smoke test when run as script
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    from data_pipeline import (
        load_listening_history, clean_listening_history, summarise_listening,
    )
    from music_age import (
        enrich_with_catalogue, compute_music_age, era_distribution,
        top_track_per_decade, assign_era_profile,
    )

    print("Loading and cleaning…")
    clean = clean_listening_history(load_listening_history("StreamingHistory_sample.json"))
    stats = summarise_listening(clean)

    print("Enriching…")
    enriched, _ = enrich_with_catalogue(clean, "catalogue/spotify_data.csv")

    print("Computing…")
    age     = compute_music_age(enriched)
    dist    = era_distribution(enriched)
    top     = top_track_per_decade(enriched)
    profile = assign_era_profile(dist)

    print("Rendering poster…")
    render_poster(
        age=age,
        era_dist=dist,
        top_per_decade=top,
        listening_df=enriched,
        profile=profile,
        listening_stats=stats,
        out_path="my_music_age_poster.png",
    )
    print("Saved to my_music_age_poster.png")
