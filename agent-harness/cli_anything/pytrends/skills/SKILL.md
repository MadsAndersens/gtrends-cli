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
  - image
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

### plot - Saved Trend Charts
Save an interest-over-time chart image for one or more keywords.

```bash
cli-anything-pytrends plot "python,javascript" --geo US --timeframe "today 12-m" --path output/trends.png
```

### report - Composite Dossier (one call, structured JSON)
Run the standard four-section dossier (interest over time, multi-geo, related queries,
interest by region) for a single keyword in one call. Replaces 4 sequential calls
agents would otherwise stitch together by hand.

```bash
# Defaults: timeframe=today 12-m, geos=US,GB,DE,FR,JP, all sections, top 10 related
cli-anything-pytrends --json report "wegovy"

# Subset of sections
cli-anything-pytrends --json report "ozempic" --include iot,related

# Custom geos and timeframe
cli-anything-pytrends --json report "bitcoin" --timeframe "today 5-y" --geos US,GB,DE,JP,IN
```

Output shape (JSON):

```json
{
  "keyword": "wegovy",
  "timeframe": "today 12-m",
  "geos": ["US", "GB", "DE", "FR", "JP"],
  "sections": ["iot", "multi_geo", "related", "by_region"],
  "interest_over_time": [...],
  "multi_geo": { "keywords": [...], "results": { "US": [...], "GB": [...], ... } },
  "related_queries": { "wegovy": { "top": [...], "rising": [...] } },
  "interest_by_region": [...],
  "errors": { "by_region": "..." }   // only present if a section failed
}
```

Continues on per-section failure: rate-limited or failing sections appear under `errors`,
successful sections still return data. Per-section results are individually cached, so
re-running the same report mostly hits disk.

**Options:**
- `--timeframe STR` : default `today 12-m`
- `--geos STR` : comma-separated geos for the multi_geo section (default `US,GB,DE,FR,JP`)
- `--include STR` : subset of `iot,multi_geo,related,by_region`
- `--top-related N` : cap top/rising rows per keyword (default 10)
- `--cat`, `--gprop`, `--wait-time` : as in other commands

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
- Use `plot --path FILE` when the user needs an image chart saved to disk
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
