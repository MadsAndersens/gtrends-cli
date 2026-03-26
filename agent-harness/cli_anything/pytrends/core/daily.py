"""Daily data fetching with monthly scaling for pytrends CLI harness."""

import pandas as pd

from pytrends.dailydata import get_daily_data


def fetch_daily(
    keyword: str,
    start_year: int,
    start_month: int,
    stop_year: int,
    stop_month: int,
    geo: str = "US",
    wait_time: float = 5.0,
    verbose: bool = False,
) -> pd.DataFrame:
    """Fetch daily Google Trends data with monthly scaling.

    Returns a DataFrame with columns:
    - {keyword}: Scaled daily search volume
    - {keyword}_unscaled: Original daily data
    - {keyword}_monthly: Monthly data used for scaling
    - scale: The scale factor applied
    """
    return get_daily_data(
        word=keyword,
        start_year=start_year,
        start_mon=start_month,
        stop_year=stop_year,
        stop_mon=stop_month,
        geo=geo,
        verbose=verbose,
        wait_time=wait_time,
    )
