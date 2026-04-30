"""Plot generation for pytrends CLI harness."""

from pathlib import Path
from typing import Optional

import pandas as pd

from cli_anything.pytrends.core.session import Session


def save_interest_over_time_plot(
    session: Session,
    output_path: str,
    title: Optional[str] = None,
) -> dict:
    """Fetch interest-over-time data and save it as a line plot."""
    if session.payload is None:
        raise RuntimeError("No payload configured. Run a plot command with keywords first.")

    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as e:
        raise RuntimeError("Plotting requires matplotlib. Install cli-anything-pytrends with plot support.") from e

    df = session.client.interest_over_time()
    if df is None or df.empty:
        raise RuntimeError("No trend data returned; cannot create plot.")

    plot_df = _prepare_plot_data(df)
    if plot_df.empty or len(plot_df.columns) == 0:
        raise RuntimeError("Trend data did not include plottable keyword columns.")

    path = Path(output_path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)

    payload = session.payload
    plot_title = title or _default_title(payload.kw_list, payload.geo, payload.timeframe)

    fig, ax = plt.subplots(figsize=(10, 6))
    plot_df.plot(ax=ax, linewidth=2)
    ax.set_title(plot_title)
    ax.set_xlabel("Date")
    ax.set_ylabel("Interest")
    ax.set_ylim(bottom=0)
    ax.grid(True, axis="y", alpha=0.3)
    ax.legend(title="Keyword")
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    return {
        "path": str(path.resolve()),
        "keywords": payload.kw_list,
        "geo": payload.geo,
        "timeframe": payload.timeframe,
        "rows": len(plot_df),
        "columns": list(plot_df.columns),
    }


def _prepare_plot_data(df: pd.DataFrame) -> pd.DataFrame:
    """Remove pytrends metadata columns from interest-over-time data."""
    return df.drop(columns=["isPartial"], errors="ignore")


def _default_title(keywords: list, geo: str, timeframe: str) -> str:
    scope = geo or "worldwide"
    return f"Google Trends: {', '.join(keywords)} ({scope}, {timeframe})"
