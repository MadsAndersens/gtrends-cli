"""Plot generation for pytrends CLI harness."""

import math
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

    plt = _import_matplotlib()

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
    ax.legend(
        title="Keyword",
        loc="upper center",
        bbox_to_anchor=(0.5, -0.15),
        ncol=max(1, len(plot_df.columns)),
        frameon=False,
    )
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


def save_multi_geo_plot(
    multi_geo_result: dict,
    output_path: str,
    title: Optional[str] = None,
) -> dict:
    """Save a faceted grid plot — one panel per country, lines per keyword.

    Each country has its own y-axis (0–100) because Google Trends values are
    not comparable across geos; faceting prevents misreading them as such.
    """
    plt = _import_matplotlib()

    results = multi_geo_result.get("results") or {}
    panels = [(geo, _prepare_plot_data(df)) for geo, df in results.items()]
    panels = [(geo, df) for geo, df in panels if df is not None and not df.empty and len(df.columns) > 0]
    if not panels:
        raise RuntimeError("No trend data returned for any geo; cannot create plot.")

    keywords = list(multi_geo_result.get("keywords") or panels[0][1].columns)
    timeframe = multi_geo_result.get("timeframe", "")

    n = len(panels)
    ncols = min(n, max(1, math.ceil(math.sqrt(n))))
    nrows = math.ceil(n / ncols)

    path = Path(output_path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(
        nrows, ncols,
        figsize=(5 * ncols, 3.2 * nrows),
        sharex=False,
        sharey=True,
        squeeze=False,
    )
    flat_axes = axes.flatten()

    handles_by_label: dict = {}
    for ax, (geo, df) in zip(flat_axes, panels):
        df.plot(ax=ax, linewidth=1.8, legend=False)
        ax.set_title(geo)
        ax.set_ylim(0, 100)
        ax.grid(True, axis="y", alpha=0.3)
        ax.set_xlabel("")
        ax.set_ylabel("")
        h, l = ax.get_legend_handles_labels()
        for handle, label in zip(h, l):
            handles_by_label.setdefault(label, handle)

    for ax in flat_axes[n:]:
        ax.set_visible(False)

    for row in range(nrows):
        flat_axes[row * ncols].set_ylabel("Interest")
    last_row_start = (nrows - 1) * ncols
    for col in range(ncols):
        idx = last_row_start + col
        if idx < n:
            flat_axes[idx].set_xlabel("Date")

    suptitle = title or _default_multi_geo_title(keywords, list(results.keys()), timeframe)
    fig.suptitle(suptitle)

    ordered_labels = [k for k in keywords if k in handles_by_label]
    ordered_handles = [handles_by_label[k] for k in ordered_labels]
    fig.legend(
        ordered_handles,
        ordered_labels,
        title="Keyword",
        loc="lower center",
        bbox_to_anchor=(0.5, 0.0),
        ncol=max(1, len(ordered_labels)),
        frameon=False,
    )
    fig.tight_layout(rect=(0, 0.06, 1, 0.96))
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    return {
        "path": str(path.resolve()),
        "keywords": keywords,
        "geos": [geo for geo, _ in panels],
        "timeframe": timeframe,
        "panels": n,
    }


def _import_matplotlib():
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as e:
        raise RuntimeError("Plotting requires matplotlib. Install cli-anything-pytrends with plot support.") from e
    return plt


def _prepare_plot_data(df: pd.DataFrame) -> pd.DataFrame:
    """Remove pytrends metadata columns from interest-over-time data."""
    return df.drop(columns=["isPartial"], errors="ignore")


def _default_title(keywords: list, geo: str, timeframe: str) -> str:
    scope = geo or "worldwide"
    return f"Google Trends: {', '.join(keywords)} ({scope}, {timeframe})"


def _default_multi_geo_title(keywords: list, geos: list, timeframe: str) -> str:
    scope = ", ".join(geos) if geos else "selected geos"
    return f"Google Trends: {', '.join(keywords)} ({scope}, {timeframe})"
