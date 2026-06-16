TRACK_ALIASES = {
    "monza": "Monza",
    "monaco": "Monaco",
    "silverstone": "Silverstone",

    "Monza": "Monza",
    "Monaco": "Monaco",
    "Silverstone": "Silverstone",
}


def normalize_track_name(track_name: str) -> str:
    """
    Convert user/environment track names into the exact format
    expected by the data layer.
    """
    cleaned = track_name.strip()

    if cleaned in TRACK_ALIASES:
        return TRACK_ALIASES[cleaned]

    lowered = cleaned.lower()
    if lowered in TRACK_ALIASES:
        return TRACK_ALIASES[lowered]

    available = sorted({"Monza", "Monaco", "Silverstone"})
    raise ValueError(
        f"Unknown track '{track_name}'. Available tracks: {available}"
    )