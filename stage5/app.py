
"""
app.py
------
Stage 5 of the "My Music Age" project.

A simple file-input wrapper around the Stages 2-4 pipeline. The user
provides the path to their Spotify export file; the function runs
the full pipeline and renders the poster.

Built using ONLY syllabus-covered tools:
  - Functions with default arguments      (Module 1, L10)
  - Conditional logic                     (Module 1, L8)
  - Exception handling (try/except)       (Module 1, L12)
  - input() for user prompts              (Module 1, L4)
  - Path / file existence checks          (Module 1, L13)

No ipywidgets, no event handlers, no IPython.display.
The interactivity is the input() prompt + re-running the cell.

Public API:
    run(json_path=None) -> dict
        Runs the full pipeline. If json_path is None, asks the user.

    interactive()
        A simple prompt-driven session: asks the user for a file path,
        runs the pipeline, and prints a summary.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

# Pipeline imports — modules from earlier stages
from data_pipeline import (
    load_listening_history,
    clean_listening_history,
    summarise_listening,
)
from music_age import (
    enrich_with_catalogue,
    compute_music_age,
    era_distribution,
    top_track_per_decade,
    assign_era_profile,
)
from wrapped_poster import render_poster


# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------

CATALOGUE_PATH = "catalogue/spotify_data.csv"
SAMPLE_PATH    = "StreamingHistory_sample.json"
DEFAULT_OUTPUT = "my_music_age_poster.png"


# ---------------------------------------------------------------------------
# CORE — runs the full Stages 2-4 pipeline end-to-end
# ---------------------------------------------------------------------------

def run(json_path: str = SAMPLE_PATH,
        output_png: str = DEFAULT_OUTPUT,
        verbose: bool = True) -> dict:
    """
    Run the full My Music Age pipeline on a Spotify history file.

    Args:
        json_path  : path to a Spotify StreamingHistory JSON file
        output_png : where to save the poster (default: my_music_age_poster.png)
        verbose    : if True, prints progress messages at each step

    Returns:
        a summary dict containing the headline numbers and statistics.
    """
    # 1. Validate the input file exists. Module 1, L8 conditionals + L13 file handling
    if not Path(json_path).exists():
        raise FileNotFoundError(
            f"File not found: {json_path}\n"
            f"Hint: place your Spotify export in the same folder as this notebook, "
            f"or use the sample file '{SAMPLE_PATH}'."
        )

    if verbose:
        print(f"Loading {json_path}…")

    # 2. Stage 2: load + clean
    raw   = load_listening_history(json_path)
    clean = clean_listening_history(raw)
    listen_stats = summarise_listening(clean)

    if clean.empty:
        raise ValueError("No usable plays after cleaning. Is this a Spotify export?")

    if verbose:
        print(f"  Cleaned: {len(clean):,} plays")

    # 3. Stage 3: enrich + compute
    if verbose:
        print(f"Enriching with catalogue ({CATALOGUE_PATH})…")
    enriched, match_stats = enrich_with_catalogue(clean, CATALOGUE_PATH)

    if verbose:
        print(f"  Match rate: {match_stats['match_rate_plays']}% of plays")
        print("Computing Music Age…")

    age     = compute_music_age(enriched)
    dist    = era_distribution(enriched)
    top     = top_track_per_decade(enriched)
    profile = assign_era_profile(dist)

    # 4. Stage 4: render the poster
    if verbose:
        print("Rendering poster…")
    fig = render_poster(
        age=age,
        era_dist=dist,
        top_per_decade=top,
        listening_df=enriched,
        profile=profile,
        listening_stats=listen_stats,
        out_path=output_png,
    )

    # Show inline (Jupyter will pick this up; if running as a script,
    # plt.show() blocks until the window is closed)
    plt.show()

    summary = {
        "music_age_weighted":  age.get("music_age_weighted"),
        "music_age_library":   age.get("music_age_library"),
        "era_profile":         profile,
        "total_plays":         len(clean),
        "matched_plays":       match_stats["matched_plays"],
        "match_rate":          match_stats["match_rate_plays"],
        "total_hours":         round(listen_stats["total_minutes"] / 60, 1),
        "poster_saved_to":     output_png,
    }

    if verbose:
        print()
        print(f"  Music Age (weighted): {summary['music_age_weighted']} years")
        print(f"  Music Age (library):  {summary['music_age_library']} years")
        print(f"  Era Profile:          {summary['era_profile']}")
        print(f"  Total listening:      {summary['total_hours']:.1f} hours")
        print(f"  Poster saved to:      {summary['poster_saved_to']}")

    return summary


# ---------------------------------------------------------------------------
# INTERACTIVE — prompt-driven session for live demos
# ---------------------------------------------------------------------------

def interactive() -> dict | None:
    """
    A simple input()-driven session.

    Asks the user for a file path. If they hit Enter without typing,
    the sample file is used. Then runs the full pipeline.

    Demonstrates Module 1 fundamentals: input(), conditionals,
    string methods, and exception handling.
    """
    print("=" * 50)
    print("  🎧  My Music Age")
    print("=" * 50)
    print()
    print("Enter the path to your Spotify export JSON file.")
    print(f"(Or press Enter to use the sample: {SAMPLE_PATH})")
    print()

    user_input = input("File path: ").strip()

    # Conditional: empty input → use sample. Module 1, L8.
    if user_input == "":
        path = SAMPLE_PATH
        print(f"Using sample data ({path})\n")
    else:
        path = user_input
        print(f"Using {path}\n")

    # Run the pipeline with exception handling. Module 1, L12.
    try:
        return run(path)
    except FileNotFoundError as e:
        print(f"\n  ✗ {e}")
        return None
    except ValueError as e:
        print(f"\n  ✗ Invalid file: {e}")
        return None


# ---------------------------------------------------------------------------
# Smoke test when run as script
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Direct call with the sample file — no input prompt
    run(SAMPLE_PATH)
