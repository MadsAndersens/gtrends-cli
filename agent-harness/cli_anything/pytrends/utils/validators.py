"""Input validation utilities for pytrends CLI harness."""

import re

VALID_GPROPS = {"", "images", "news", "youtube", "froogle"}
VALID_RESOLUTIONS = {"COUNTRY", "REGION", "DMA", "CITY"}

TIMEFRAME_PATTERNS = [
    r"^today \d+-[dmy]$",
    r"^now \d+-[dH]$",
    r"^\d{4}-\d{2}-\d{2} \d{4}-\d{2}-\d{2}$",
    r"^all$",
]


def validate_gprop(gprop: str) -> str:
    """Validate and return the gprop value."""
    if gprop not in VALID_GPROPS:
        raise ValueError(
            f"Invalid gprop '{gprop}'. Must be one of: {', '.join(repr(g) for g in sorted(VALID_GPROPS))}"
        )
    return gprop


def validate_resolution(resolution: str) -> str:
    """Validate and return the resolution value."""
    resolution = resolution.upper()
    if resolution not in VALID_RESOLUTIONS:
        raise ValueError(
            f"Invalid resolution '{resolution}'. Must be one of: {', '.join(sorted(VALID_RESOLUTIONS))}"
        )
    return resolution


def validate_timeframe(timeframe: str) -> str:
    """Validate and return the timeframe value."""
    for pattern in TIMEFRAME_PATTERNS:
        if re.match(pattern, timeframe):
            return timeframe
    raise ValueError(
        f"Invalid timeframe '{timeframe}'. Examples: 'today 5-y', 'today 3-m', "
        "'now 1-d', '2023-01-01 2023-12-31', 'all'"
    )


def parse_keywords(kw_string: str) -> list:
    """Parse a comma-separated keyword string into a list."""
    keywords = [kw.strip() for kw in kw_string.split(",")]
    keywords = [kw for kw in keywords if kw]
    if not keywords:
        raise ValueError("At least one keyword is required.")
    if len(keywords) > 5:
        raise ValueError("Google Trends allows a maximum of 5 keywords per query.")
    return keywords
