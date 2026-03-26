"""cli-anything-pytrends: CLI harness for Google Trends via pytrends.

Usage:
    cli-anything-pytrends [OPTIONS] COMMAND [ARGS]...
    cli-anything-pytrends repl  (interactive mode)
"""

import json
import os
import sys
import traceback

import click

from cli_anything.pytrends import __version__
from cli_anything.pytrends.core.session import Session, SessionConfig
from cli_anything.pytrends.utils.formatting import format_output
from cli_anything.pytrends.utils.validators import (
    parse_keywords,
    validate_gprop,
    validate_resolution,
    validate_timeframe,
)

# Global session (for REPL persistence)
_session: Session = None


def _get_session(ctx: click.Context) -> Session:
    """Get or create the session from click context."""
    global _session
    if _session is None:
        _session = Session()
    return _session


def _output(ctx: click.Context, data, label: str = "result"):
    """Format and print output based on context flags."""
    fmt = ctx.obj.get("format", "table")
    output_path = ctx.obj.get("output")
    try:
        formatted = format_output(data, fmt)
        if output_path:
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(formatted)
                f.write("\n")
            click.echo(f"Saved to {output_path}", err=True)
        else:
            click.echo(formatted)
    except Exception as e:
        if fmt == "json":
            click.echo(json.dumps({"error": str(e)}))
        else:
            click.echo(f"Error formatting output: {e}", err=True)


def _handle_error(ctx: click.Context, e: Exception):
    """Handle errors with appropriate formatting."""
    fmt = ctx.obj.get("format", "table")
    msg = str(e)

    # Provide actionable hints for common Google Trends errors
    hint = ""
    if "code 404" in msg:
        hint = " (this Google Trends endpoint may be deprecated upstream)"
    elif "code 429" in msg or "TooManyRequests" in type(e).__name__:
        hint = " (rate limited — wait a moment or use: session init --retries 3 --backoff-factor 1)"

    if fmt == "json":
        err = {"error": msg + hint, "type": type(e).__name__}
        click.echo(json.dumps(err))
    else:
        click.echo(f"Error: {msg}{hint}", err=True)
    if not isinstance(e, (ValueError, RuntimeError)):
        sys.exit(1)


# ── Root Group ──────────────────────────────────────────────────────────

@click.group(invoke_without_command=True)
@click.option("--json", "use_json", is_flag=True, help="Output in JSON format")
@click.option("--csv", "use_csv", is_flag=True, help="Output in CSV format")
@click.option("--output", "-o", "output_path", default=None, type=click.Path(), help="Write output to FILE instead of stdout")
@click.version_option(version=__version__, prog_name="cli-anything-pytrends")
@click.pass_context
def cli(ctx, use_json, use_csv, output_path):
    """CLI harness for Google Trends via pytrends."""
    ctx.ensure_object(dict)
    if use_json:
        ctx.obj["format"] = "json"
    elif use_csv:
        ctx.obj["format"] = "csv"
    else:
        ctx.obj["format"] = "table"
    ctx.obj["output"] = output_path

    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


# ── Session Commands ────────────────────────────────────────────────────

@cli.group()
@click.pass_context
def session(ctx):
    """Manage the pytrends session configuration."""
    pass


@session.command("init")
@click.option("--hl", default="en-US", help="Language/locale (e.g., en-US, es-ES)")
@click.option("--tz", default=360, type=int, help="Timezone offset in minutes")
@click.option("--geo", default="", help="Geographic region (e.g., US, GB)")
@click.option("--timeout", default="2,5", help="Timeout as connect,read (seconds)")
@click.option("--proxies", default="", help="Proxy URL(s), comma-separated")
@click.option("--retries", default=0, type=int, help="Number of retries")
@click.option("--backoff-factor", default=0.0, type=float, help="Retry backoff factor")
@click.pass_context
def session_init(ctx, hl, tz, geo, timeout, proxies, retries, backoff_factor):
    """Initialize a new pytrends session with the given configuration."""
    global _session
    try:
        timeout_parts = tuple(int(x.strip()) for x in timeout.split(","))
        if len(timeout_parts) == 1:
            timeout_parts = (timeout_parts[0], timeout_parts[0])

        config = SessionConfig(
            hl=hl, tz=tz, geo=geo, timeout=timeout_parts,
            proxies=proxies, retries=retries, backoff_factor=backoff_factor,
        )
        _session = Session(config)
        # Force initialization by accessing the client
        _ = _session.client
        _output(ctx, _session.get_status())
    except Exception as e:
        _handle_error(ctx, e)


@session.command("show")
@click.pass_context
def session_show(ctx):
    """Show the current session configuration."""
    s = _get_session(ctx)
    _output(ctx, s.get_status())


@session.command("set")
@click.argument("key")
@click.argument("value")
@click.pass_context
def session_set(ctx, key, value):
    """Set a session configuration value (e.g., session set hl es-ES)."""
    s = _get_session(ctx)
    try:
        if key == "tz":
            value = int(value)
        elif key == "retries":
            value = int(value)
        elif key == "backoff_factor":
            value = float(value)
        elif key == "timeout":
            value = tuple(int(x.strip()) for x in value.split(","))
        s.reinit(**{key: value})
        _output(ctx, s.get_status())
    except Exception as e:
        _handle_error(ctx, e)


# ── Search Commands ─────────────────────────────────────────────────────

@cli.group()
@click.pass_context
def search(ctx):
    """Search Google Trends for keyword interest data."""
    pass


@search.command("interest-over-time")
@click.argument("keywords")
@click.option("--cat", default=0, type=int, help="Category ID (0 = all)")
@click.option("--timeframe", default="today 5-y", help="Time range (e.g., 'today 5-y')")
@click.option("--geo", default="", help="Geographic region")
@click.option("--gprop", default="", help="Search property (images, news, youtube, froogle)")
@click.pass_context
def search_iot(ctx, keywords, cat, timeframe, geo, gprop):
    """Fetch interest over time for KEYWORDS (comma-separated, max 5)."""
    s = _get_session(ctx)
    try:
        kw_list = parse_keywords(keywords)
        validate_gprop(gprop)
        validate_timeframe(timeframe)
        s.build_payload(kw_list=kw_list, cat=cat, timeframe=timeframe, geo=geo, gprop=gprop)
        from cli_anything.pytrends.core.search import interest_over_time
        result = interest_over_time(s)
        _output(ctx, result)
    except Exception as e:
        _handle_error(ctx, e)


@search.command("interest-by-region")
@click.argument("keywords")
@click.option("--cat", default=0, type=int, help="Category ID (0 = all)")
@click.option("--timeframe", default="today 5-y", help="Time range")
@click.option("--geo", default="", help="Geographic region")
@click.option("--gprop", default="", help="Search property")
@click.option("--resolution", default="COUNTRY", help="Resolution: COUNTRY, REGION, DMA, CITY")
@click.option("--inc-low-vol", is_flag=True, help="Include low volume areas")
@click.option("--inc-geo-code", is_flag=True, help="Include geographic codes")
@click.pass_context
def search_ibr(ctx, keywords, cat, timeframe, geo, gprop, resolution, inc_low_vol, inc_geo_code):
    """Fetch interest by region for KEYWORDS (comma-separated, max 5)."""
    s = _get_session(ctx)
    try:
        kw_list = parse_keywords(keywords)
        validate_gprop(gprop)
        validate_timeframe(timeframe)
        resolution = validate_resolution(resolution)
        s.build_payload(kw_list=kw_list, cat=cat, timeframe=timeframe, geo=geo, gprop=gprop)
        from cli_anything.pytrends.core.search import interest_by_region
        result = interest_by_region(s, resolution=resolution, inc_low_vol=inc_low_vol, inc_geo_code=inc_geo_code)
        _output(ctx, result)
    except Exception as e:
        _handle_error(ctx, e)


@search.command("multirange")
@click.argument("keywords")
@click.option("--cat", default=0, type=int, help="Category ID (0 = all)")
@click.option("--timeframes", required=True, help="Semicolon-separated timeframes")
@click.option("--geo", default="", help="Geographic region")
@click.option("--gprop", default="", help="Search property")
@click.pass_context
def search_multirange(ctx, keywords, cat, timeframes, geo, gprop):
    """Fetch interest over time across multiple time ranges for KEYWORDS."""
    s = _get_session(ctx)
    try:
        kw_list = parse_keywords(keywords)
        validate_gprop(gprop)
        tf_list = [tf.strip() for tf in timeframes.split(";")]
        for tf in tf_list:
            validate_timeframe(tf)
        s.build_payload(kw_list=kw_list, cat=cat, timeframe=tf_list, geo=geo, gprop=gprop)
        from cli_anything.pytrends.core.search import multirange_interest_over_time
        result = multirange_interest_over_time(s)
        _output(ctx, result)
    except Exception as e:
        _handle_error(ctx, e)


# ── Related Commands ────────────────────────────────────────────────────

@cli.group()
@click.pass_context
def related(ctx):
    """Find related topics and queries for keywords."""
    pass


@related.command("topics")
@click.argument("keywords")
@click.option("--cat", default=0, type=int, help="Category ID")
@click.option("--timeframe", default="today 5-y", help="Time range")
@click.option("--geo", default="", help="Geographic region")
@click.option("--gprop", default="", help="Search property")
@click.pass_context
def related_topics_cmd(ctx, keywords, cat, timeframe, geo, gprop):
    """Fetch related topics for KEYWORDS (comma-separated, max 5)."""
    s = _get_session(ctx)
    try:
        kw_list = parse_keywords(keywords)
        validate_gprop(gprop)
        validate_timeframe(timeframe)
        s.build_payload(kw_list=kw_list, cat=cat, timeframe=timeframe, geo=geo, gprop=gprop)
        from cli_anything.pytrends.core.related import related_topics
        result = related_topics(s)
        _output(ctx, result)
    except Exception as e:
        _handle_error(ctx, e)


@related.command("queries")
@click.argument("keywords")
@click.option("--cat", default=0, type=int, help="Category ID")
@click.option("--timeframe", default="today 5-y", help="Time range")
@click.option("--geo", default="", help="Geographic region")
@click.option("--gprop", default="", help="Search property")
@click.pass_context
def related_queries_cmd(ctx, keywords, cat, timeframe, geo, gprop):
    """Fetch related queries for KEYWORDS (comma-separated, max 5)."""
    s = _get_session(ctx)
    try:
        kw_list = parse_keywords(keywords)
        validate_gprop(gprop)
        validate_timeframe(timeframe)
        s.build_payload(kw_list=kw_list, cat=cat, timeframe=timeframe, geo=geo, gprop=gprop)
        from cli_anything.pytrends.core.related import related_queries
        result = related_queries(s)
        _output(ctx, result)
    except Exception as e:
        _handle_error(ctx, e)


# ── Trending Commands ───────────────────────────────────────────────────

@cli.group()
@click.pass_context
def trending(ctx):
    """Discover trending searches on Google."""
    pass


@trending.command("now")
@click.option("--pn", default="united_states", help="Country name (e.g., united_states, united_kingdom)")
@click.pass_context
def trending_now(ctx, pn):
    """Fetch currently hot/trending searches. (May be deprecated by Google.)"""
    s = _get_session(ctx)
    try:
        from cli_anything.pytrends.core.trending import trending_searches
        result = trending_searches(s, pn=pn)
        _output(ctx, result)
    except Exception as e:
        _handle_error(ctx, e)


@trending.command("today")
@click.option("--pn", default="US", help="Country code (e.g., US, GB)")
@click.pass_context
def trending_today(ctx, pn):
    """Fetch today's trending searches. (May be deprecated by Google.)"""
    s = _get_session(ctx)
    try:
        from cli_anything.pytrends.core.trending import today_searches
        result = today_searches(s, pn=pn)
        _output(ctx, result)
    except Exception as e:
        _handle_error(ctx, e)


@trending.command("realtime")
@click.option("--pn", default="US", help="Country code (e.g., US, IN)")
@click.option("--cat", default="all", help="Category filter")
@click.option("--count", default=300, type=int, help="Number of results (max 300)")
@click.pass_context
def trending_realtime(ctx, pn, cat, count):
    """Fetch real-time trending searches. (May be deprecated by Google.)"""
    s = _get_session(ctx)
    try:
        from cli_anything.pytrends.core.trending import realtime_trending_searches
        result = realtime_trending_searches(s, pn=pn, cat=cat, count=count)
        _output(ctx, result)
    except Exception as e:
        _handle_error(ctx, e)


# ── Explore Commands ────────────────────────────────────────────────────

@cli.group()
@click.pass_context
def explore(ctx):
    """Explore suggestions, categories, and top charts."""
    pass


@explore.command("suggestions")
@click.argument("keyword")
@click.pass_context
def explore_suggestions(ctx, keyword):
    """Get autocomplete suggestions for KEYWORD."""
    s = _get_session(ctx)
    try:
        from cli_anything.pytrends.core.explore import suggestions
        result = suggestions(s, keyword)
        _output(ctx, result)
    except Exception as e:
        _handle_error(ctx, e)


@explore.command("categories")
@click.pass_context
def explore_categories(ctx):
    """List all available Google Trends categories."""
    s = _get_session(ctx)
    try:
        from cli_anything.pytrends.core.explore import categories
        result = categories(s)
        _output(ctx, result)
    except Exception as e:
        _handle_error(ctx, e)


@explore.command("top-charts")
@click.argument("year", type=int)
@click.option("--hl", default="en-US", help="Language/locale")
@click.option("--tz", default=300, type=int, help="Timezone offset")
@click.option("--geo", default="GLOBAL", help="Geographic region")
@click.pass_context
def explore_top_charts(ctx, year, hl, tz, geo):
    """Get top charts for YEAR (e.g., 2023)."""
    s = _get_session(ctx)
    try:
        from cli_anything.pytrends.core.explore import top_charts
        result = top_charts(s, date=year, hl=hl, tz=tz, geo=geo)
        _output(ctx, result)
    except Exception as e:
        _handle_error(ctx, e)


# ── Daily Command ───────────────────────────────────────────────────────

@cli.command("daily")
@click.argument("keyword")
@click.option("--start", required=True, help="Start date as YYYY-MM (e.g., 2023-01)")
@click.option("--stop", required=True, help="Stop date as YYYY-MM (e.g., 2023-12)")
@click.option("--geo", default="US", help="Geographic region")
@click.option("--wait-time", default=5.0, type=float, help="Wait time between requests (seconds)")
@click.pass_context
def daily_cmd(ctx, keyword, start, stop, geo, wait_time):
    """Fetch daily data with monthly scaling for KEYWORD."""
    try:
        start_parts = start.split("-")
        stop_parts = stop.split("-")
        start_year, start_month = int(start_parts[0]), int(start_parts[1])
        stop_year, stop_month = int(stop_parts[0]), int(stop_parts[1])

        from cli_anything.pytrends.core.daily import fetch_daily
        result = fetch_daily(
            keyword=keyword,
            start_year=start_year,
            start_month=start_month,
            stop_year=stop_year,
            stop_month=stop_month,
            geo=geo,
            wait_time=wait_time,
        )
        _output(ctx, result)
    except Exception as e:
        _handle_error(ctx, e)


# ── REPL Mode ──────────────────────────────────────────────────────────

@cli.command("repl")
@click.pass_context
def repl(ctx):
    """Start an interactive REPL session."""
    click.echo(f"cli-anything-pytrends v{__version__} - Interactive Mode")
    click.echo("Type 'help' for commands, 'quit' to exit.\n")

    # Initialize session
    _get_session(ctx)

    while True:
        try:
            line = input("pytrends> ").strip()
        except (EOFError, KeyboardInterrupt):
            click.echo("\nGoodbye!")
            break

        if not line:
            continue
        if line in ("quit", "exit", "q"):
            click.echo("Goodbye!")
            break
        if line == "help":
            click.echo(_repl_help())
            continue

        # Parse and dispatch REPL commands
        parts = line.split()
        cmd = parts[0]
        args = parts[1:]

        try:
            _dispatch_repl(ctx, cmd, args)
        except SystemExit:
            pass  # Click raises SystemExit on --help, etc.
        except Exception as e:
            click.echo(f"Error: {e}", err=True)


def _repl_help() -> str:
    return """Available commands:
  session init [--hl X] [--tz N] [--geo X]    Initialize session
  session show                                  Show session config
  session set KEY VALUE                         Update session config

  search iot KEYWORDS [--timeframe X] ...       Interest over time
  search ibr KEYWORDS [--resolution X] ...      Interest by region
  search multirange KEYWORDS --timeframes X     Multi-range interest

  related topics KEYWORDS [--timeframe X]       Related topics
  related queries KEYWORDS [--timeframe X]      Related queries

  trending now [--pn X]                         Hot searches
  trending today [--pn X]                       Today's searches
  trending realtime [--pn X] [--cat X]          Real-time trends

  explore suggestions KEYWORD                   Autocomplete suggestions
  explore categories                            List categories
  explore top-charts YEAR                       Top charts for year

  daily KEYWORD --start YYYY-MM --stop YYYY-MM  Daily scaled data

  help                                          Show this help
  quit                                          Exit REPL
"""


def _dispatch_repl(ctx: click.Context, cmd: str, args: list):
    """Dispatch a REPL command to the appropriate Click command."""
    # Map REPL shortcuts to full Click command paths
    lookup = {
        "session": session,
        "search": search,
        "related": related,
        "trending": trending,
        "explore": explore,
        "daily": daily_cmd,
    }

    # Shorthand mappings
    shorthand = {
        "iot": ["search", "interest-over-time"],
        "ibr": ["search", "interest-by-region"],
        "suggestions": ["explore", "suggestions"],
        "categories": ["explore", "categories"],
    }

    if cmd in shorthand:
        full = shorthand[cmd]
        cmd = full[0]
        args = full[1:] + args

    if cmd in lookup:
        group_or_cmd = lookup[cmd]
        try:
            # For groups, pass remaining args through
            group_or_cmd.main(args, parent=ctx, standalone_mode=False)
        except click.exceptions.UsageError as e:
            click.echo(f"Usage error: {e}")
    else:
        click.echo(f"Unknown command: {cmd}. Type 'help' for available commands.")


def main():
    """Entry point for the CLI."""
    cli(obj={})


if __name__ == "__main__":
    main()
