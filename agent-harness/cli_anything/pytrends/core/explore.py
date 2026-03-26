"""Exploration and discovery commands for pytrends CLI harness.

Suggestions, categories, and top charts.
"""

import pandas as pd

from cli_anything.pytrends.core.session import Session


def suggestions(session: Session, keyword: str) -> list:
    """Get keyword suggestions from Google Trends autocomplete."""
    return session.client.suggestions(keyword)


def categories(session: Session) -> dict:
    """Get all available Google Trends categories."""
    return session.client.categories()


def top_charts(
    session: Session,
    date: int,
    hl: str = "en-US",
    tz: int = 300,
    geo: str = "GLOBAL",
) -> pd.DataFrame:
    """Get top charts for a given year."""
    return session.client.top_charts(date=date, hl=hl, tz=tz, geo=geo)
