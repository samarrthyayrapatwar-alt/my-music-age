"""
wrapped_poster.py
-----------------
Stage 4 of the "My Music Age" project.

Renders a single-page, Spotify Wrapped-style poster summarising the
user's Music Age report. The poster is the deliverable: a PNG image
suitable for slides, social sharing, and the GitHub README.

Public API:
    render_poster(age, era_dist, top_per_decade, listening_df,
                  profile, out_path=None) -> matplotlib.figure.Figure

Design choices are documented inline. Customisation points (colours,
fonts, dimensions) are at the top of this file as constants so the
whole palette can be retuned in one place without hunting through code.
"""

from __future__ import annotations

from pathlib import Path
from typing import Union

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.patches import FancyBboxPatch
import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# DESIGN CONSTANTS
# ---------------------------------------------------------------------------

# Spotify-inspired palette. Kept together so the palette can be
# swapped entirely by editing this one block.
BG_COLOR        = "#121212"    # deep black background
PANEL_COLOR     = "#1E1E1E"    # slightly lighter cards
ACCENT_COLOR    = "#1DB954"    # Spotify green — used sparingly for emphasis
MUTED_COLOR     = "#535353"    # Spotify's standard "muted gray"
TEXT_PRIMARY    = "#F0F0F0"    # off-white (softer than pure white)
TEXT_SECONDARY  = "#A7A7A7"    # light gray for labels and footers
DIVIDER_COLOR   = "#2A2A2A"    # faint separator lines

# Typography. Uses matplotlib's DejaVu Sans which ships with every
# installation, so no font dependency issues.
FONT_FAMILY = "DejaVu Sans"

# Poster dimensions: portrait, 2:3 aspect ratio — presentations friendly.
POSTER_W_IN = 8
POSTER_H_IN = 12

# DPI for the saved PNG. 200 gives a crisp output for slides without
# producing massive files. Bump to 300 for print-quality posters.
POSTER_DPI = 200


# ---------------------------------------------------------------------------
# HELPERS — little visual building blocks
# ---------------------------------------------------------------------------

def _style_axes(ax: plt.Axes) -> None:
    """
    Remove all chrome (spines, ticks, background) from an axes.
    We draw our panels by hand inside them, so matplotlib's default
    decorations would fight us.
    """
    ax.set_facecolor(BG_COLOR)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_xticks([])
    ax.set_yticks([])


def _rounded_panel(ax: plt.Axes) -> None:
    """
    Draw a soft rounded rectangle filling the axes as a subtle card
    background. Mimics Spotify UI cards.
    """
    rect = FancyBboxPatch(
        (0.01, 0.01),
        0.98, 0.98,
        boxstyle="round,pad=0.01,rounding_size=0.02",
        transform=ax.transAxes,
        facecolor=PANEL_COLOR,
        edgecolor="none",
        zorder=0,
    )
    ax.add_patch(rect)


# ---------------------------------------------------------------------------
# PANEL RENDERERS — each draws one section of the poster
# ---------------------------------------------------------------------------

def _draw_header(ax: plt.Axes, age: dict, profile: str) -> None:
    """
    Top panel: project title + HERO Music Age number + profile label.
    The hero number is intentionally enormous — this is the one thing
    the viewer should remember.
    """
    _style_axes(ax)

    # Tiny eyebrow label
    ax.text(
        0.5, 0.95,
        "MY MUSIC AGE",
        ha="center", va="top",
        color=TEXT_SECONDARY,
        fontsize=11,
        family=FONT_FAMILY,
        fontweight="bold",
        transform=ax.transAxes,
    )

    # HERO number — the weighted Music Age in huge type
    weighted = age.get("music_age_weighted")
    hero_text = f"{weighted:.1f}" if weighted is not None else "—"
    ax.text(
        0.5, 0.58,
        hero_text,
        ha="center", va="center",
        color=ACCENT_COLOR,
        fontsize=110,
        family=FONT_FAMILY,
        fontweight="bold",
        transform=ax.transAxes,
    )

    ax.text(
        0.5, 0.28,
        "YEARS",
        ha="center", va="center",
        color=TEXT_PRIMARY,
        fontsize=16,
        family=FONT_FAMILY,
        fontweight="bold",
        transform=ax.transAxes,
    )

    # Era profile tagline
    ax.text(
        0.5, 0.10,
        profile.upper(),
        ha="center", va="center",
        color=TEXT_PRIMARY,
        fontsize=18,
        family=FONT_FAMILY,
        fontweight="normal",
        style="italic",
        transform=ax.transAxes,
    )


def _draw_subages(ax: plt.Axes, age: dict) -> None:
    """
    Small two-column callout: weighted vs library age side-by-side.
    Two numbers tell a story ('how old my listening is' vs 'how old
    my taste is') that one number can't.
    """
    _style_axes(ax)
    _rounded_panel(ax)

    # Left half — weighted
    ax.text(0.25, 0.72, "WEIGHTED", ha="center", va="center",
            color=TEXT_SECONDARY, fontsize=9, fontweight="bold",
            family=FONT_FAMILY, transform=ax.transAxes)
    ax.text(0.25, 0.42,
            f"{age['music_age_weighted']:.1f}" if age["music_age_weighted"] is not None else "—",
            ha="center", va="center",
            color=TEXT_PRIMARY, fontsize=28, fontweight="bold",
            family=FONT_FAMILY, transform=ax.transAxes)
    ax.text(0.25, 0.18, "what you play most", ha="center", va="center",
            color=TEXT_SECONDARY, fontsize=8,
            family=FONT_FAMILY, transform=ax.transAxes)

    # Divider — thin vertical line
    ax.plot([0.5, 0.5], [0.15, 0.85], color=DIVIDER_COLOR, lw=1,
            transform=ax.transAxes)

    # Right half — library
    ax.text(0.75, 0.72, "LIBRARY", ha="center", va="center",
            color=TEXT_SECONDARY, fontsize=9, fontweight="bold",
            family=FONT_FAMILY, transform=ax.transAxes)
    ax.text(0.75, 0.42,
            f"{age['music_age_library']:.1f}" if age["music_age_library"] is not None else "—",
            ha="center", va="center",
            color=TEXT_PRIMARY, fontsize=28, fontweight="bold",
            family=FONT_FAMILY, transform=ax.transAxes)
    ax.text(0.75, 0.18, "your whole taste", ha="center", va="center",
            color=TEXT_SECONDARY, fontsize=8,
            family=FONT_FAMILY, transform=ax.transAxes)


def _draw_era_bars(ax: plt.Axes, era_dist: pd.DataFrame) -> None:
    """
    Horizontal bar chart of era distribution. The dominant decade is
    highlighted in green; others are muted gray. One accent, not a
    rainbow — it's the decade that matters.
    """
    _style_axes(ax)
    _rounded_panel(ax)

    # Title
    ax.text(0.04, 0.93, "ERAS YOU LIVE IN",
            ha="left", va="top",
            color=TEXT_SECONDARY, fontsize=10, fontweight="bold",
            family=FONT_FAMILY, transform=ax.transAxes)

    if era_dist.empty:
        ax.text(0.5, 0.5, "No matched tracks",
                ha="center", va="center",
                color=TEXT_SECONDARY, fontsize=12,
                transform=ax.transAxes)
        return

    # Work in axes-fraction coordinates so the panel scales cleanly
    # if we ever change the grid dimensions.
    decades = era_dist["decade"].tolist()
    pcts    = era_dist["pct_of_total"].tolist()
    top_idx = int(np.argmax(pcts))

    n = len(decades)
    # Allocate vertical space for bars, leaving room for the title
    top_y = 0.82
    bot_y = 0.08
    row_h = (top_y - bot_y) / n
    label_x = 0.10
    bar_x   = 0.22
    bar_max = 0.68   # width of the bar track
    pct_x   = 0.94

    # Scale bars to the max percentage (not 100) so small distributions
    # don't look tiny. Makes the chart always feel visually balanced.
    max_pct = max(pcts) if pcts else 1
    for i, (decade, pct) in enumerate(zip(decades, pcts)):
        y = top_y - (i + 0.5) * row_h
        width = (pct / max_pct) * bar_max if max_pct > 0 else 0
        color = ACCENT_COLOR if i == top_idx else MUTED_COLOR

        # Decade label on the left
        ax.text(label_x, y, decade,
                ha="right", va="center",
                color=TEXT_PRIMARY,
                fontsize=11, fontweight="bold",
                family=FONT_FAMILY, transform=ax.transAxes)

        # The bar itself — drawn as a rounded-corner rectangle
        # Minimum width ensures tiny percentages remain visible
        bar = FancyBboxPatch(
            (bar_x, y - row_h * 0.22),
            max(width, 0.015),  # never narrower than ~1.5% of the panel
            row_h * 0.45,
            boxstyle="round,pad=0,rounding_size=0.006",
            transform=ax.transAxes,
            facecolor=color,
            edgecolor="none",
            zorder=2,
        )
        ax.add_patch(bar)

        # Percentage label on the right
        ax.text(pct_x, y, f"{pct:.1f}%",
                ha="right", va="center",
                color=TEXT_PRIMARY if i == top_idx else TEXT_SECONDARY,
                fontsize=10, fontweight="bold" if i == top_idx else "normal",
                family=FONT_FAMILY, transform=ax.transAxes)


def _draw_top_tracks(ax: plt.Axes, top_per_decade: pd.DataFrame) -> None:
    """
    List of top tracks per decade. Clean, left-aligned list with
    decade-in-green-accent, artist name in bold, track name under it.
    """
    _style_axes(ax)
    _rounded_panel(ax)

    ax.text(0.04, 0.94, "TOP TRACK PER ERA",
            ha="left", va="top",
            color=TEXT_SECONDARY, fontsize=10, fontweight="bold",
            family=FONT_FAMILY, transform=ax.transAxes)

    if top_per_decade.empty:
        ax.text(0.5, 0.5, "No matched tracks",
                ha="center", va="center",
                color=TEXT_SECONDARY, fontsize=12,
                transform=ax.transAxes)
        return

    # Render chronologically, newest first (felt more natural — recent tracks
    # at the top draw the eye first).
    rows = top_per_decade.sort_values("decade", ascending=False)

    n = len(rows)
    top_y = 0.82
    bot_y = 0.08
    row_h = (top_y - bot_y) / n

    for i, (_, r) in enumerate(rows.iterrows()):
        y = top_y - (i + 0.5) * row_h

        # Decade tag — small, green
        ax.text(0.05, y, r["decade"],
                ha="left", va="center",
                color=ACCENT_COLOR, fontsize=10, fontweight="bold",
                family=FONT_FAMILY, transform=ax.transAxes)

        # Track title — slightly above row centre
        track = r["track"]
        if len(track) > 30:
            track = track[:28] + "…"
        ax.text(0.20, y + row_h * 0.22, track,
                ha="left", va="center",
                color=TEXT_PRIMARY, fontsize=10, fontweight="bold",
                family=FONT_FAMILY, transform=ax.transAxes)

        # Artist — smaller, muted, below the track
        artist = r["artist"]
        if len(artist) > 28:
            artist = artist[:26] + "…"
        ax.text(0.20, y - row_h * 0.22, artist,
                ha="left", va="center",
                color=TEXT_SECONDARY, fontsize=8,
                family=FONT_FAMILY, transform=ax.transAxes)


def _draw_heatmap(ax: plt.Axes, listening_df: pd.DataFrame) -> None:
    """
    A 7x24 heatmap (day-of-week × hour-of-day) showing when the user
    actually listens. Green-intensity = more minutes.

    This isn't strictly about Music Age but it's a beautiful, immediately
    readable artefact — and it's syllabus content (heatmap from groupby).
    """
    _style_axes(ax)
    _rounded_panel(ax)

    ax.text(0.04, 0.93, "WHEN YOU LISTEN",
            ha="left", va="top",
            color=TEXT_SECONDARY, fontsize=10, fontweight="bold",
            family=FONT_FAMILY, transform=ax.transAxes)

    # Aggregate minutes by day × hour
    day_order = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    day_full  = ["Monday", "Tuesday", "Wednesday", "Thursday",
                 "Friday", "Saturday", "Sunday"]

    if "day_of_week" not in listening_df.columns or "hour" not in listening_df.columns:
        return

    grid = (listening_df
            .groupby(["day_of_week", "hour"])["minutes_played"]
            .sum()
            .unstack(fill_value=0)
            .reindex(index=day_full, columns=range(24), fill_value=0))

    data = grid.to_numpy()
    vmax = data.max() if data.max() > 0 else 1

    # Custom green-only colormap: fade from muted gray → Spotify green
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list(
        "spotify_heat",
        [MUTED_COLOR, ACCENT_COLOR],
    )

    # Draw heatmap in an inset so the panel title has space above it
    # and row/column labels have space on the left/bottom.
    inset = ax.inset_axes([0.10, 0.20, 0.85, 0.62])
    inset.set_facecolor(BG_COLOR)
    for s in inset.spines.values():
        s.set_visible(False)
    im = inset.imshow(data, aspect="auto", cmap=cmap, vmin=0, vmax=vmax)

    inset.set_yticks(range(7))
    inset.set_yticklabels(day_order, color=TEXT_SECONDARY,
                          fontsize=9, family=FONT_FAMILY)
    # Show only 0, 6, 12, 18 as hour ticks — cleaner
    hour_ticks = [0, 6, 12, 18]
    inset.set_xticks(hour_ticks)
    inset.set_xticklabels([f"{h:02d}" for h in hour_ticks],
                          color=TEXT_SECONDARY, fontsize=9, family=FONT_FAMILY)
    inset.tick_params(length=0, pad=6)

    # Subtle axis label positioned outside the inset area
    ax.text(0.5, 0.02, "HOUR OF DAY",
            ha="center", va="bottom",
            color=TEXT_SECONDARY, fontsize=7,
            family=FONT_FAMILY, transform=ax.transAxes)


def _draw_footer(ax: plt.Axes, age: dict, stats: dict) -> None:
    """
    Minimal footer with the source-of-truth numbers and generator credit.
    Keeps the poster honest about how many plays produced the result.
    """
    _style_axes(ax)

    usable_plays = age.get("usable_plays", 0)
    usable_tracks = age.get("usable_tracks", 0)
    total_minutes = stats.get("total_minutes", 0)

    hours_total = total_minutes / 60

    line = (f"Generated from {usable_plays:,} matched plays across "
            f"{usable_tracks} unique tracks · "
            f"{hours_total:,.0f} hours of listening")

    ax.text(0.5, 0.7, line,
            ha="center", va="center",
            color=TEXT_SECONDARY, fontsize=9,
            family=FONT_FAMILY, transform=ax.transAxes)

    ax.text(0.5, 0.25,
            "My Music Age · Programming in Python · Vidyashilp University",
            ha="center", va="center",
            color=TEXT_SECONDARY, fontsize=8, style="italic",
            family=FONT_FAMILY, transform=ax.transAxes)


# ---------------------------------------------------------------------------
# PUBLIC — the one function that assembles everything
# ---------------------------------------------------------------------------

def render_poster(
    age: dict,
    era_dist: pd.DataFrame,
    top_per_decade: pd.DataFrame,
    listening_df: pd.DataFrame,
    profile: str,
    listening_stats: dict | None = None,
    out_path: Union[str, Path, None] = None,
) -> mpl.figure.Figure:
    """
    Build the My Music Age poster as a single matplotlib Figure.

    Args:
        age              — dict from compute_music_age()
        era_dist         — DataFrame from era_distribution()
        top_per_decade   — DataFrame from top_track_per_decade()
        listening_df     — the cleaned listening DataFrame (for heatmap)
        profile          — era profile string from assign_era_profile()
        listening_stats  — optional dict from summarise_listening()
                           (used in the footer line)
        out_path         — if given, save a PNG here too

    Returns the Figure so the caller can display it inline in a notebook
    (just leaving it un-`plt.show()`-ed works in Jupyter).
    """
    if listening_stats is None:
        listening_stats = {"total_minutes": listening_df["minutes_played"].sum()}

    fig = plt.figure(figsize=(POSTER_W_IN, POSTER_H_IN),
                     facecolor=BG_COLOR)

    # 6-row × 1-col grid. Heights chosen by eye:
    #   header (tall, hero)
    #   subages (small)
    #   era bars (medium)
    #   top tracks (tallish)
    #   heatmap (medium)
    #   footer (tiny)
    gs = GridSpec(
        6, 1,
        figure=fig,
        height_ratios=[3.0, 1.0, 2.8, 3.4, 2.8, 0.4],
        hspace=0.18,
        left=0.06, right=0.94, top=0.97, bottom=0.03,
    )

    _draw_header(fig.add_subplot(gs[0]), age, profile)
    _draw_subages(fig.add_subplot(gs[1]), age)
    _draw_era_bars(fig.add_subplot(gs[2]), era_dist)
    _draw_top_tracks(fig.add_subplot(gs[3]), top_per_decade)
    _draw_heatmap(fig.add_subplot(gs[4]), listening_df)
    _draw_footer(fig.add_subplot(gs[5]), age, listening_stats)

    if out_path:
        fig.savefig(
            out_path,
            dpi=POSTER_DPI,
            facecolor=BG_COLOR,
            bbox_inches="tight",
            pad_inches=0.15,
        )

    return fig


# ---------------------------------------------------------------------------
# Smoke test when run as script
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    from data_pipeline import load_listening_history, clean_listening_history, summarise_listening
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
    fig = render_poster(
        age=age,
        era_dist=dist,
        top_per_decade=top,
        listening_df=enriched,
        profile=profile,
        listening_stats=stats,
        out_path="my_music_age_poster.png",
    )
    print("Saved to my_music_age_poster.png")
