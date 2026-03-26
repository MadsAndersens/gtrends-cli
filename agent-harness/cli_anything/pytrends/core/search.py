"""Search operations for pytrends CLI harness.

Handles interest_over_time, interest_by_region, and multirange queries.
"""

import pandas as pd

from cli_anything.pytrends.core.session import Session


def interest_over_time(session: Session) -> pd.DataFrame:
    """Fetch interest over time data for the current payload."""
    if session.payload is None:
        raise RuntimeError("No payload configured. Run a search command with keywords first.")
    return session.client.interest_over_time()


def interest_by_region(
    session: Session,
    resolution: str = "COUNTRY",
    inc_low_vol: bool = False,
    inc_geo_code: bool = False,
) -> pd.DataFrame:
    """Fetch interest by region data for the current payload."""
    if session.payload is None:
        raise RuntimeError("No payload configured. Run a search command with keywords first.")
    return session.client.interest_by_region(
        resolution=resolution,
        inc_low_vol=inc_low_vol,
        inc_geo_code=inc_geo_code,
    )


def multirange_interest_over_time(session: Session) -> pd.DataFrame:
    """Fetch multirange interest over time data for the current payload."""
    if session.payload is None:
        raise RuntimeError("No payload configured. Run a search command with keywords first.")
    return session.client.multirange_interest_over_time()
