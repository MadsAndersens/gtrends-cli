"""Exploration and discovery commands for pytrends CLI harness.

Suggestions, categories, and top charts.
"""

import pandas as pd

from cli_anything.pytrends.core.cache import cached_call
from cli_anything.pytrends.core.session import Session


def suggestions(session: Session, keyword: str) -> list:
    """Get keyword suggestions from Google Trends autocomplete."""
    return cached_call(
        session.cache,
        session.cache_ttl,
        "explore.suggestions",
        {"hl": session.config.hl, "tz": session.config.tz, "keyword": keyword},
        lambda: session.client.suggestions(keyword),
    )


def categories(session: Session) -> dict:
    """Get all available Google Trends categories."""
    return cached_call(
        session.cache,
        session.cache_ttl,
        "explore.categories",
        {"hl": session.config.hl, "tz": session.config.tz},
        lambda: session.client.categories(),
    )


def top_charts(
    session: Session,
    date: int,
    hl: str = "en-US",
    tz: int = 300,
    geo: str = "GLOBAL",
) -> pd.DataFrame:
    """Get top charts for a given year."""
    return cached_call(
        session.cache,
        session.cache_ttl,
        "explore.top_charts",
        {"date": date, "hl": hl, "tz": tz, "geo": geo},
        lambda: session.client.top_charts(date=date, hl=hl, tz=tz, geo=geo),
    )
