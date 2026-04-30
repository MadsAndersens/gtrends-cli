"""Search operations for pytrends CLI harness.

Handles interest_over_time, interest_by_region, multirange, and multi-geo queries.
"""

import time

import click
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


def multi_geo_interest_over_time(
    session: Session,
    kw_list: list,
    geos: list,
    cat: int = 0,
    timeframe: str = "today 5-y",
    gprop: str = "",
    wait_time: float = 1.0,
) -> dict:
    """Fetch interest over time for keywords across multiple geographic regions.

    Each geo gets its own API call with all keywords together, so keyword
    interest values are relative to each other within each country.
    """
    results = {}
    errors = {}

    for i, geo in enumerate(geos):
        click.echo(f"[{i + 1}/{len(geos)}] Fetching {geo}...", err=True)
        try:
            session.build_payload(
                kw_list=kw_list, cat=cat, timeframe=timeframe, geo=geo, gprop=gprop,
            )
            df = session.client.interest_over_time()
            if not df.empty and "isPartial" in df.columns:
                df = df.drop(columns=["isPartial"])
            results[geo] = df
        except Exception as e:
            errors[geo] = str(e)
            click.echo(f"  Warning: {geo} failed — {e}", err=True)

        # Wait between requests to avoid rate limiting (skip after last)
        if i < len(geos) - 1 and wait_time > 0:
            time.sleep(wait_time)

    output = {
        "keywords": kw_list,
        "timeframe": timeframe,
        "geos": list(results.keys()),
        "results": results,
    }
    if errors:
        output["errors"] = errors

    return output
