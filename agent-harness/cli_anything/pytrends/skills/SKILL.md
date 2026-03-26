---
name: cli-anything-pytrends
version: 0.1.0
description: CLI harness for Google Trends data via pytrends
binary: cli-anything-pytrends
install: pip install cli-anything-pytrends
source: https://github.com/GeneralMills/pytrends
tags:
  - google-trends
  - data
  - analytics
  - search-trends
  - cli
output_formats:
  - table
  - json
  - csv
---

# cli-anything-pytrends

CLI tool for querying Google Trends data. Wraps the pytrends library to provide
command-line access to all Google Trends endpoints with structured output.

## Command Groups

### session - Session Management
Manage the pytrends session configuration (language, timezone, geo, proxies).

```bash
cli-anything-pytrends session init --hl en-US --tz 360 --geo US
cli-anything-pytrends session show
cli-anything-pytrends session set hl es-ES
```

### search - Keyword Interest Data
Query Google Trends for keyword interest over time and by region.

```bash
# Interest over time (default: last 5 years)
cli-anything-pytrends search interest-over-time "python,javascript"
cli-anything-pytrends search interest-over-time "AI" --timeframe "today 3-m" --geo US

# Interest by region
cli-anything-pytrends search interest-by-region "python" --resolution COUNTRY
cli-anything-pytrends search interest-by-region "python" --resolution CITY --geo US

# Multi-range comparison
cli-anything-pytrends search multirange "python" --timeframes "today 3-m;today 12-m"
```

**Options for search commands:**
- `--cat N` : Category ID (0 = all, default)
- `--timeframe STR` : Time range (`today 5-y`, `today 3-m`, `2023-01-01 2023-12-31`)
- `--geo STR` : Geographic region (`US`, `GB`, `US-NY`)
- `--gprop STR` : Search property (`""`, `images`, `news`, `youtube`, `froogle`)
- `--resolution STR` : Region resolution (`COUNTRY`, `REGION`, `DMA`, `CITY`)

### related - Related Topics & Queries
Find what people also search for alongside your keywords.

```bash
cli-anything-pytrends related topics "machine learning"
cli-anything-pytrends related queries "AI" --timeframe "today 12-m"
```

### trending - Trending Searches
Discover what's trending on Google right now.

```bash
cli-anything-pytrends trending now --pn united_states
cli-anything-pytrends trending today --pn US
cli-anything-pytrends trending realtime --pn US --cat all --count 100
```

### explore - Discovery
Explore suggestions, categories, and top charts.

```bash
cli-anything-pytrends explore suggestions "python programming"
cli-anything-pytrends explore categories
cli-anything-pytrends explore top-charts 2023 --geo GLOBAL
```

### daily - Daily Scaled Data
Fetch daily data with monthly scaling for accurate long-term comparison.

```bash
cli-anything-pytrends daily "bitcoin" --start 2023-01 --stop 2023-12 --geo US
```

## Output Modes

All commands support three output formats via global flags:

```bash
# Human-readable table (default)
cli-anything-pytrends trending now

# JSON for programmatic consumption
cli-anything-pytrends --json trending now

# CSV for data pipelines
cli-anything-pytrends --csv search interest-over-time "python"
```

## Agent Usage Notes

- Keywords are comma-separated, max 5 per query (Google Trends limit)
- Use `--json` for all agent-consumed output — structured and parseable
- `search` and `related` commands auto-call `build_payload` — no separate setup needed
- `trending`, `explore`, and `daily` commands are standalone (no payload required)
- Rate limiting: Google Trends may return 429 errors; use `session init --retries 3 --backoff-factor 1`
- REPL mode (`cli-anything-pytrends repl`) is for interactive human use, not agents

## Timeframe Reference

| Format | Example | Description |
|--------|---------|-------------|
| `today N-d` | `today 7-d` | Last N days |
| `today N-m` | `today 3-m` | Last N months |
| `today N-y` | `today 5-y` | Last N years |
| `now N-d` | `now 1-d` | Last N days (real-time) |
| `now N-H` | `now 4-H` | Last N hours (real-time) |
| `YYYY-MM-DD YYYY-MM-DD` | `2023-01-01 2023-12-31` | Custom range |
| `all` | `all` | All available data |
