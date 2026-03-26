# PYTRENDS CLI Harness - Standard Operating Procedure

## Overview

**pytrends** is a Python library (v4.9.2) providing a pseudo-API for Google Trends.
It wraps Google Trends' internal HTTP endpoints and returns pandas DataFrames.

This CLI harness (`cli-anything-pytrends`) exposes all pytrends functionality as
a stateful command-line tool with JSON output mode for agent consumption.

## Architecture

### Source Library

- **Core class:** `pytrends.request.TrendReq`
- **Data model:** pandas DataFrames / dicts of DataFrames
- **HTTP layer:** requests sessions with retry/proxy support
- **Exceptions:** `ResponseError`, `TooManyRequestsError`

### CLI Command Groups

| Group | Commands | Description |
|-------|----------|-------------|
| `session` | `init`, `show`, `set` | Manage TrendReq session (hl, tz, geo, proxies) |
| `search` | `interest-over-time`, `interest-by-region`, `multirange` | Keyword-based searches (require build_payload) |
| `related` | `topics`, `queries` | Related topics and queries for keywords |
| `trending` | `now`, `today`, `realtime` | Trending/hot searches (standalone) |
| `explore` | `suggestions`, `categories`, `top-charts` | Discovery and exploration |
| `daily` | `fetch` | Daily data with monthly scaling (dailydata.py) |

### State Model

The CLI maintains a session state:
- **TrendReq instance** with configurable hl, tz, geo, timeout, proxies, retries
- **Current payload** (kw_list, cat, timeframe, geo, gprop) set via `search` commands
- **REPL mode** for interactive exploration

### Output Formats

- **Table** (default): Human-readable pandas DataFrame rendering
- **JSON** (`--json`): Machine-readable output for agent consumption
- **CSV** (`--csv`): CSV export for data pipelines

### Key Design Decisions

1. All commands accept `--json` for structured output
2. `search` and `related` commands accept keywords inline (auto-call build_payload)
3. Session state persists across REPL commands
4. Proxy rotation and retry are configurable at session level
5. Error messages include actionable remediation hints

## Timeframe Format Reference

| Format | Example | Description |
|--------|---------|-------------|
| `today N-d` | `today 7-d` | Last N days |
| `today N-m` | `today 3-m` | Last N months |
| `today N-y` | `today 5-y` | Last N years (default) |
| `YYYY-MM-DD YYYY-MM-DD` | `2023-01-01 2023-12-31` | Custom date range |
| `now N-d` | `now 1-d` | Last N days (real-time) |
| `now N-H` | `now 4-H` | Last N hours (real-time) |

## gprop Values

| Value | Search Property |
|-------|----------------|
| (empty) | Web Search |
| `images` | Image Search |
| `news` | News Search |
| `youtube` | YouTube Search |
| `froogle` | Google Shopping |

## Resolution Values (interest_by_region)

| Value | Scope |
|-------|-------|
| `COUNTRY` | Country level (default) |
| `REGION` | State/Province level |
| `DMA` | Designated Market Area (US only) |
| `CITY` | City level (US only) |
