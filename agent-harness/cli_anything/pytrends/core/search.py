"""Search operations for pytrends CLI harness.

Handles interest_over_time, interest_by_region, multirange, and multi-geo queries.
"""

import time

import click
import pandas as pd

from cli_anything.pytrends.core.cache import cached_call
from cli_anything.pytrends.core.session import Session


def interest_over_time(session: Session) -> pd.DataFrame:
    """Fetch interest over time data for the current payload."""
    if session.payload is None:
        raise RuntimeError("No payload configured. Run a search command with keywords first.")
    return cached_call(
        session.cache,
        session.cache_ttl,
        "search.interest_over_time",
        session.cache_key_inputs(),
        lambda: session.client.interest_over_time(),
    )


def interest_by_region(
    session: Session,
    resolution: str = "COUNTRY",
    inc_low_vol: bool = False,
    inc_geo_code: bool = False,
) -> pd.DataFrame:
    """Fetch interest by region data for the current payload."""
    if session.payload is None:
        raise RuntimeError("No payload configured. Run a search command with keywords first.")
    extra = {
        "resolution": resolution,
        "inc_low_vol": inc_low_vol,
        "inc_geo_code": inc_geo_code,
    }
    return cached_call(
        session.cache,
        session.cache_ttl,
        "search.interest_by_region",
        session.cache_key_inputs(extra),
        lambda: session.client.interest_by_region(
            resolution=resolution,
            inc_low_vol=inc_low_vol,
            inc_geo_code=inc_geo_code,
        ),
    )


def multirange_interest_over_time(session: Session) -> pd.DataFrame:
    """Fetch multirange interest over time data for the current payload."""
    if session.payload is None:
        raise RuntimeError("No payload configured. Run a search command with keywords first.")
    return cached_call(
        session.cache,
        session.cache_ttl,
        "search.multirange_interest_over_time",
        session.cache_key_inputs(),
        lambda: session.client.multirange_interest_over_time(),
    )


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
    interest values are relative to each other within each country. Per-geo
    results are cached individually so a partial failure can be retried
    without re-fetching the geos that already succeeded.
    """
    results = {}
    errors = {}
    any_miss = False

    for i, geo in enumerate(geos):
        click.echo(f"[{i + 1}/{len(geos)}] Fetching {geo}...", err=True)
        try:
            session.build_payload(
                kw_list=kw_list, cat=cat, timeframe=timeframe, geo=geo, gprop=gprop,
            )

            def fetch_geo():
                df = session.client.interest_over_time()
                if not df.empty and "isPartial" in df.columns:
                    df = df.drop(columns=["isPartial"])
                return df

            df = cached_call(
                session.cache,
                session.cache_ttl,
                "search.multi_geo_interest_over_time.per_geo",
                session.cache_key_inputs(),
                fetch_geo,
            )
            from cli_anything.pytrends.core.cache import last_was_cache_hit
            if not last_was_cache_hit():
                any_miss = True
            results[geo] = df
        except Exception as e:
            any_miss = True
            errors[geo] = str(e)
            click.echo(f"  Warning: {geo} failed — {e}", err=True)

        # Wait between requests only when we actually hit the network.
        if i < len(geos) - 1 and wait_time > 0 and any_miss:
            time.sleep(wait_time)

    output = {
        "keywords": kw_list,
        "timeframe": timeframe,
        "geos": list(results.keys()),
        "results": results,
    }
    if errors:
        output["errors"] = errors

    # Mark the aggregate as a hit only when every geo came from cache and
    # nothing failed.
    from cli_anything.pytrends.core.cache import _record_hit
    _record_hit(not any_miss and not errors)

    return output
