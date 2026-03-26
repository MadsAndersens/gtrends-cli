# gtrends-cli

A command-line interface for accessing Google Trends data, built on top of the [pytrends](https://github.com/GeneralMills/pytrends) library. Supports multiple output formats (table, JSON, CSV), stateful sessions, and an interactive REPL mode.

## Installation

```bash
cd agent-harness
pip install -e .
```

Requires Python 3.8+. This creates the `cli-anything-pytrends` console command.

## Quick Start

```bash
# Search interest over time
cli-anything-pytrends search interest-over-time "python,javascript"

# Get trending searches
cli-anything-pytrends trending now --pn united_states

# Output as JSON for scripting
cli-anything-pytrends --json search interest-over-time "AI"

# Launch interactive mode
cli-anything-pytrends repl
```

## Commands

### search — Keyword-based trend queries

```bash
# Interest over time (default: last 5 years)
cli-anything-pytrends search interest-over-time "python,javascript" --timeframe "today 3-m"

# Interest by region
cli-anything-pytrends search interest-by-region "machine learning" --resolution COUNTRY

# Multi-range comparison
cli-anything-pytrends search multirange "AI" --timeframes "today 1-y;today 5-y"
```

Options: `--cat`, `--timeframe`, `--geo`, `--gprop`

### related — Related topics and queries

```bash
cli-anything-pytrends related topics "cryptocurrency"
cli-anything-pytrends related queries "cryptocurrency" --timeframe "today 1-y"
```

### trending — Hot and trending searches

```bash
cli-anything-pytrends trending now --pn united_states
cli-anything-pytrends trending today --pn US
cli-anything-pytrends trending realtime --pn US --count 50
```

### explore — Discovery and suggestions

```bash
cli-anything-pytrends explore suggestions "bitcoin"
cli-anything-pytrends explore categories
cli-anything-pytrends explore top-charts 2023
```

### daily — Daily search volume with monthly scaling

```bash
cli-anything-pytrends daily "tesla" --start 2023-01 --stop 2023-12
```

### session — Manage session configuration

```bash
cli-anything-pytrends session init --hl en-US --tz 360
cli-anything-pytrends session show
cli-anything-pytrends session set hl es-ES
```

### repl — Interactive mode

```bash
cli-anything-pytrends repl

pytrends> search iot "bitcoin" --timeframe "today 3-m"
pytrends> trending realtime
pytrends> explore suggestions ethereum
pytrends> quit
```

## Output Formats

| Flag     | Format | Use case            |
|----------|--------|---------------------|
| *(none)* | Table  | Human-readable      |
| `--json` | JSON   | Scripts and agents  |
| `--csv`  | CSV    | Data pipelines      |

```bash
cli-anything-pytrends --json search interest-over-time "python"
cli-anything-pytrends --csv search interest-by-region "AI"
```

## Timeframe Reference

| Format                      | Example                      | Description              |
|-----------------------------|------------------------------|--------------------------|
| `today N-d`                 | `today 7-d`                  | Last N days              |
| `today N-m`                 | `today 3-m`                  | Last N months            |
| `today N-y`                 | `today 5-y`                  | Last N years (default)   |
| `YYYY-MM-DD YYYY-MM-DD`    | `2023-01-01 2023-12-31`      | Custom date range        |
| `now N-d`                   | `now 1-d`                    | Last N days (real-time)  |
| `now N-H`                   | `now 4-H`                    | Last N hours (real-time) |

## Project Structure

```
gtrends-cli/
├── pytrends-src/              # Upstream pytrends library (v4.9.2)
│   └── pytrends/
│       ├── request.py         # TrendReq core API
│       └── dailydata.py       # Daily data fetching
│
└── agent-harness/             # CLI harness
    ├── setup.py
    └── cli_anything/pytrends/
        ├── pytrends_cli.py    # CLI entry point (Click)
        ├── core/
        │   ├── session.py     # Stateful session management
        │   ├── search.py      # interest_over_time, interest_by_region
        │   ├── related.py     # related_topics, related_queries
        │   ├── trending.py    # trending/hot searches
        │   ├── explore.py     # suggestions, categories, top_charts
        │   └── daily.py       # daily data with scaling
        ├── utils/
        │   ├── formatting.py  # Table/JSON/CSV output
        │   └── validators.py  # Input validation
        └── tests/
            ├── test_core.py       # Unit tests
            └── test_full_e2e.py   # End-to-end tests
```

## Running Tests

```bash
cd agent-harness
pytest -v
```

## Caveats

- Google Trends uses unofficial endpoints that may change without notice.
- Rate limiting (HTTP 429) can occur — configure retries and backoff via session settings.
- Daily data fetching requires sequential monthly requests and can be slow.
- Maximum of 5 keywords per query.

## License

MIT (CLI harness) / Apache 2.0 (pytrends)
