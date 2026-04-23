"""
generate_sample_data.py
-----------------------
Creates a realistic fake Spotify listening-history JSON file that matches
Spotify's Account Privacy export format exactly.

Output schema (list of dicts):
    [
        {
            "endTime":    "YYYY-MM-DD HH:MM",
            "artistName": str,
            "trackName":  str,
            "msPlayed":   int
        },
        ...
    ]

Why we need this:
  Real Spotify data takes 1–30 days to arrive via email request.
  This lets us develop and test the entire pipeline immediately,
  then swap in the real file with ZERO code changes later.

Design choices that make it feel real:
  - ~15000 plays over 1 year (typical heavy listener)
  - A curated "taste library" mixing several eras (so Music Age is interesting)
  - Skip-throughs: ~8% of plays are very short (< 30s)
  - Listening peaks on evenings and weekends
  - Favourite songs repeat; obscure ones play once
  - Some noisy / case-inconsistent strings so the cleaner has work to do
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path


# ---------------------------------------------------------------------------
# 1. A curated "taste library" the fake user listens to
#    Each entry: (artist, track, era_bias) — era_bias just helps us
#    pick realistic release years later when we build the catalogue.
# ---------------------------------------------------------------------------
TASTE_LIBRARY = [
    # Heavy-rotation favourites (each will play many times)
    ("Arctic Monkeys",        "Do I Wanna Know?",              "2010s"),
    ("Arctic Monkeys",        "R U Mine?",                     "2010s"),
    ("The Weeknd",            "Blinding Lights",               "2020s"),
    ("The Weeknd",            "Save Your Tears",               "2020s"),
    ("Taylor Swift",          "Cruel Summer",                  "2010s"),
    ("Taylor Swift",          "Anti-Hero",                     "2020s"),
    ("Billie Eilish",         "lovely",                        "2010s"),
    ("Billie Eilish",         "What Was I Made For?",          "2020s"),
    ("Dua Lipa",              "Levitating",                    "2020s"),

    # 2000s mainstays
    ("Coldplay",              "Yellow",                        "2000s"),
    ("Coldplay",              "Fix You",                       "2000s"),
    ("Linkin Park",           "In The End",                    "2000s"),
    ("Linkin Park",           "Numb",                          "2000s"),
    ("Green Day",             "Boulevard of Broken Dreams",    "2000s"),

    # 90s nostalgia
    ("Nirvana",               "Smells Like Teen Spirit",       "1990s"),
    ("Oasis",                 "Wonderwall",                    "1990s"),
    ("Radiohead",             "Creep",                         "1990s"),
    ("Red Hot Chili Peppers", "Under the Bridge",              "1990s"),

    # 80s classics
    ("Queen",                 "Bohemian Rhapsody",             "1970s"),
    ("Queen",                 "Don't Stop Me Now",             "1970s"),
    ("Michael Jackson",       "Billie Jean",                   "1980s"),
    ("Michael Jackson",       "Thriller",                      "1980s"),
    ("a-ha",                  "Take On Me",                    "1980s"),
    ("Journey",               "Don't Stop Believin'",          "1980s"),

    # 70s deep cuts
    ("Fleetwood Mac",         "Dreams",                        "1970s"),
    ("Pink Floyd",            "Wish You Were Here",            "1970s"),
    ("Led Zeppelin",          "Stairway to Heaven",            "1970s"),

    # 60s soul / classics
    ("The Beatles",           "Let It Be",                     "1960s"),
    ("The Beatles",           "Here Comes the Sun",            "1960s"),
    ("The Rolling Stones",    "Paint It Black",                "1960s"),

    # Indian / regional sprinkle for realism
    ("Arijit Singh",          "Tum Hi Ho",                     "2010s"),
    ("Arijit Singh",          "Channa Mereya",                 "2010s"),
    ("A.R. Rahman",           "Kun Faya Kun",                  "2010s"),

    # Long-tail variety (played rarely)
    ("Lana Del Rey",          "Summertime Sadness",            "2010s"),
    ("Tame Impala",           "The Less I Know The Better",    "2010s"),
    ("Frank Ocean",           "Thinkin Bout You",              "2010s"),
    ("Kendrick Lamar",        "HUMBLE.",                       "2010s"),
    ("Mac Miller",            "Good News",                     "2020s"),
    ("Harry Styles",          "As It Was",                     "2020s"),
    ("Olivia Rodrigo",        "drivers license",               "2020s"),

    # A few with deliberate string-noise so the cleaner has work to do.
    ("  arctic monkeys ",     "Do I Wanna Know?",              "2010s"),   # whitespace + case
    ("The Weeknd",            " blinding lights ",             "2020s"),   # padded
    ("taylor swift",          "anti-hero",                     "2020s"),   # lowercase
]


def build_play_weights(library: list) -> list[int]:
    """
    Assign each song a play-count weight.

    We want a realistic long-tail: a handful of songs dominate the
    listening time, a middle group is played sometimes, and a long tail
    is played rarely. This is how real music libraries behave.
    """
    # Pareto-ish: top 20% get much higher weights
    weights = []
    for i, _ in enumerate(library):
        if i < len(library) * 0.15:       # heavy rotation
            weights.append(random.randint(180, 400))
        elif i < len(library) * 0.50:     # medium
            weights.append(random.randint(40, 120))
        else:                              # long tail
            weights.append(random.randint(5, 25))
    return weights


def pick_listening_timestamp(start: datetime, end: datetime) -> datetime:
    """
    Pick a random timestamp between start and end, but biased toward
    evenings (6pm–midnight) and weekends. Makes the heatmap we build
    later look realistic instead of uniform noise.
    """
    # Uniform random day in range
    span_days = (end - start).days
    day_offset = random.randint(0, span_days)
    base = start + timedelta(days=day_offset)

    # Biased hour: weight evenings more
    hour_weights = [1, 1, 1, 1, 1, 1,        # 00-05 (night)
                    2, 3, 4, 3, 2, 2,        # 06-11 (morning)
                    3, 3, 2, 2, 3, 4,        # 12-17 (afternoon)
                    6, 7, 8, 7, 5, 3]        # 18-23 (evening peak)
    hour = random.choices(range(24), weights=hour_weights, k=1)[0]

    # Weekends get a small additional bump via an independent dice roll:
    # if we picked a weekday but rolled "weekend boost", shift to weekend
    if base.weekday() < 5 and random.random() < 0.15:
        base += timedelta(days=random.choice([5 - base.weekday(),
                                              6 - base.weekday()]))
        # clamp if we overshot
        if base > end:
            base = end

    minute = random.randint(0, 59)
    return base.replace(hour=hour, minute=minute, second=0, microsecond=0)


def generate_plays(
    library: list,
    weights: list[int],
    start: datetime,
    end: datetime,
    skip_rate: float = 0.08,
) -> list[dict]:
    """
    Build the full list of play records.
    Each record matches Spotify's real export schema exactly.
    """
    plays = []

    for (artist, track, _era), weight in zip(library, weights):
        # For each song, generate `weight` plays spread across the year
        for _ in range(weight):
            end_time = pick_listening_timestamp(start, end)

            # Is this play a skip-through? (< 30s)
            # Track length assumed ~3–4 minutes typical
            if random.random() < skip_rate:
                ms_played = random.randint(2_000, 28_000)     # 2–28 seconds
            else:
                # Full or near-full play: 1.5 to 5 minutes
                ms_played = random.randint(90_000, 300_000)

            plays.append({
                "endTime":    end_time.strftime("%Y-%m-%d %H:%M"),
                "artistName": artist,
                "trackName":  track,
                "msPlayed":   ms_played,
            })

    # Sort chronologically — this matches how Spotify exports it
    plays.sort(key=lambda p: p["endTime"])
    return plays


def main(output_path: str = "StreamingHistory_sample.json",
         seed: int = 42) -> None:
    random.seed(seed)

    # One year ending today (adjust if you want a longer window)
    end   = datetime(2026, 4, 23)
    start = end - timedelta(days=365)

    weights = build_play_weights(TASTE_LIBRARY)
    plays = generate_plays(TASTE_LIBRARY, weights, start, end)

    Path(output_path).write_text(
        json.dumps(plays, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # Quick stats so we can sanity-check the output
    total_min = sum(p["msPlayed"] for p in plays) / 1000 / 60
    print(f"✓ Wrote {len(plays):,} play records to {output_path}")
    print(f"  Date range: {plays[0]['endTime']}  →  {plays[-1]['endTime']}")
    print(f"  Total listening: {total_min:,.0f} minutes "
          f"({total_min/60:,.0f} hours)")
    print(f"  Unique artists: "
          f"{len({p['artistName'].strip().lower() for p in plays})}")
    print(f"  Unique tracks:  "
          f"{len({(p['artistName'].strip().lower(), p['trackName'].strip().lower()) for p in plays})}")


if __name__ == "__main__":
    main()
