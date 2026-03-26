# TEST PLAN - cli-anything-pytrends

## Unit Tests (test_core.py)

Synthetic data, no external dependencies. Mock all pytrends API calls.

### Session Module
- [ ] `test_session_config_defaults` - Default SessionConfig values
- [ ] `test_session_config_to_dict` - Serialization to dict
- [ ] `test_session_config_from_dict` - Deserialization from dict
- [ ] `test_payload_config_to_dict` - PayloadConfig serialization
- [ ] `test_session_init_creates_client` - Session creates TrendReq on access
- [ ] `test_session_reinit_resets_client` - reinit() clears client and payload
- [ ] `test_session_build_payload` - build_payload stores PayloadConfig
- [ ] `test_session_get_status` - Status dict structure

### Formatting Module
- [ ] `test_df_to_json_with_data` - DataFrame to JSON conversion
- [ ] `test_df_to_json_empty` - Empty DataFrame handling
- [ ] `test_series_to_json` - Series to JSON
- [ ] `test_dict_of_dfs_to_json` - Dict of DataFrames to JSON
- [ ] `test_list_to_json` - List to JSON
- [ ] `test_format_output_table` - Table output mode
- [ ] `test_format_output_json` - JSON output mode
- [ ] `test_format_output_csv` - CSV output mode

### Validators Module
- [ ] `test_validate_gprop_valid` - Valid gprop values
- [ ] `test_validate_gprop_invalid` - Invalid gprop raises ValueError
- [ ] `test_validate_resolution_valid` - Valid resolution values
- [ ] `test_validate_resolution_invalid` - Invalid resolution raises ValueError
- [ ] `test_validate_timeframe_valid` - Various valid timeframe patterns
- [ ] `test_validate_timeframe_invalid` - Invalid timeframe raises ValueError
- [ ] `test_parse_keywords_single` - Single keyword parsing
- [ ] `test_parse_keywords_multiple` - Multiple keyword parsing
- [ ] `test_parse_keywords_empty` - Empty string raises ValueError
- [ ] `test_parse_keywords_too_many` - >5 keywords raises ValueError

### Core Functions (mocked)
- [ ] `test_interest_over_time_no_payload` - Error when no payload configured
- [ ] `test_interest_by_region_no_payload` - Error when no payload configured
- [ ] `test_related_topics_no_payload` - Error when no payload configured
- [ ] `test_related_queries_no_payload` - Error when no payload configured

## E2E Tests (test_full_e2e.py)

Full CLI subprocess tests via installed command.

### CLI Basic
- [ ] `test_cli_version` - --version flag
- [ ] `test_cli_help` - --help flag
- [ ] `test_cli_session_show` - session show (no init needed)
- [ ] `test_cli_search_help` - search --help
- [ ] `test_cli_trending_help` - trending --help
- [ ] `test_cli_explore_help` - explore --help
- [ ] `test_cli_related_help` - related --help

### CLI JSON Output
- [ ] `test_cli_session_show_json` - session show --json
- [ ] `test_cli_session_init_json` - session init --json

### CLI Validation
- [ ] `test_cli_search_iot_no_keywords` - Missing keywords error
- [ ] `test_cli_search_ibr_bad_resolution` - Invalid resolution error

### Subprocess Tests
- [ ] `test_subprocess_version` - Version via subprocess
- [ ] `test_subprocess_help` - Help via subprocess
- [ ] `test_subprocess_session_show` - Session show via subprocess

## Test Results

**Date:** 2026-03-26
**Platform:** Windows 11 / Python 3.13.3 / pytest 9.0.1
**Result:** 81 passed, 0 failed (100% pass rate)

```
test_core.py (58 tests):
  TestSessionConfig      5/5 PASSED
  TestPayloadConfig      2/2 PASSED
  TestSession            6/6 PASSED
  TestFormatting        16/16 PASSED
  TestValidators        18/18 PASSED
  TestCoreFunctions      4/4 PASSED
  (+ 7 parametrized expansions)

test_full_e2e.py (23 tests):
  TestCLIBasic           8/8 PASSED
  TestCLISessionCommands 2/2 PASSED
  TestCLIValidation      4/4 PASSED
  TestCLIJsonOutput      2/2 PASSED
  TestCLISubprocess      7/7 PASSED

Total: 81 passed in 4.35s
```

### Coverage Notes

- **Unit tests**: Full coverage of session, formatting, validators, and core function error paths
- **E2E tests**: Click CliRunner + subprocess tests cover all command groups
- **Subprocess tests**: Use `_resolve_cli()` pattern, verified with installed command in PATH
- **Not covered**: Live Google Trends API calls (would require network access and rate limit management)
