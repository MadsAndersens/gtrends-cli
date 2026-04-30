"""Trending searches for pytrends CLI harness.

These are standalone methods that do not require build_payload.
"""

import pandas as pd

from cli_anything.pytrends.core.cache import cached_call
from cli_anything.pytrends.core.session import Session


def trending_searches(session: Session, pn: str = "united_states") -> pd.DataFrame:
    """Fetch currently trending (hot) searches for a country."""
    return cached_call(
        session.cache,
        session.cache_ttl,
        "trending.searches",
        {"hl": session.config.hl, "tz": session.config.tz, "pn": pn},
        lambda: session.client.trending_searches(pn=pn),
    )


def today_searches(session: Session, pn: str = "US") -> pd.Series:
    """Fetch today's trending searches for a country."""
    return cached_call(
        session.cache,
        session.cache_ttl,
        "trending.today",
        {"hl": session.config.hl, "tz": session.config.tz, "pn": pn},
        lambda: session.client.today_searches(pn=pn),
    )


def realtime_trending_searches(
    session: Session,
    pn: str = "US",
    cat: str = "all",
    count: int = 300,
) -> pd.DataFrame:
    """Fetch real-time trending searches."""
    return cached_call(
        session.cache,
        session.cache_ttl,
        "trending.realtime",
        {"hl": session.config.hl, "tz": session.config.tz, "pn": pn, "cat": cat, "count": count},
        lambda: session.client.realtime_trending_searches(pn=pn, cat=cat, count=count),
    )
