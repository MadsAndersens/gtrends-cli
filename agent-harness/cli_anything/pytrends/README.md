# cli-anything-pytrends

CLI harness for Google Trends via [pytrends](https://github.com/GeneralMills/pytrends).

## Installation

```bash
pip install -e .
```

## Usage

### One-shot commands

```bash
# Interest over time
cli-anything-pytrends search interest-over-time "python,javascript" --timeframe "today 5-y"

# Interest by region
cli-anything-pytrends search interest-by-region "python" --resolution COUNTRY

# Related topics
cli-anything-pytrends related topics "machine learning"

# Related queries
cli-anything-pytrends related queries "AI"

# Trending searches
cli-anything-pytrends trending now --pn united_states
cli-anything-pytrends trending today --pn US
cli-anything-pytrends trending realtime --pn US

# Explore
cli-anything-pytrends explore suggestions "python"
cli-anything-pytrends explore categories
cli-anything-pytrends explore top-charts 2023

# Daily data
cli-anything-pytrends daily "bitcoin" --start 2023-01 --stop 2023-06

# Session management
cli-anything-pytrends session init --hl en-US --tz 360
cli-anything-pytrends session show
cli-anything-pytrends session set hl es-ES
```

### JSON output (for agent consumption)

```bash
cli-anything-pytrends --json search interest-over-time "python"
cli-anything-pytrends --json trending now
cli-anything-pytrends --csv search interest-by-region "python"
```

### Interactive REPL

```bash
cli-anything-pytrends repl
```

In REPL mode, commands are entered without the `cli-anything-pytrends` prefix:

```
pytrends> search interest-over-time "python,javascript"
pytrends> trending now
pytrends> explore suggestions python
pytrends> quit
```

## Command Reference

| Group | Command | Description |
|-------|---------|-------------|
| `session` | `init`, `show`, `set` | Manage session config (hl, tz, geo, proxies) |
| `search` | `interest-over-time` | Interest over time for keywords |
| `search` | `interest-by-region` | Interest by geographic region |
| `search` | `multirange` | Interest across multiple time ranges |
| `related` | `topics` | Related topics for keywords |
| `related` | `queries` | Related queries for keywords |
| `trending` | `now` | Currently hot searches |
| `trending` | `today` | Today's trending searches |
| `trending` | `realtime` | Real-time trending searches |
| `explore` | `suggestions` | Autocomplete suggestions |
| `explore` | `categories` | List all categories |
| `explore` | `top-charts` | Top charts for a year |
| `daily` | (root) | Daily data with monthly scaling |

## Options

- `--json` : Output in JSON format (machine-readable)
- `--csv` : Output in CSV format
- `--version` : Show version
- `--help` : Show help for any command
