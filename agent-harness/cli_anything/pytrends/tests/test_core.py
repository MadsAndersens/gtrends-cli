"""Unit tests for cli-anything-pytrends core modules.

Uses synthetic data and mocks — no external dependencies or network calls.
"""

import json
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from cli_anything.pytrends.core.session import PayloadConfig, Session, SessionConfig
from cli_anything.pytrends.utils.formatting import (
    df_to_json,
    dict_to_json,
    format_output,
    list_to_json,
    series_to_json,
)
from cli_anything.pytrends.utils.validators import (
    parse_keywords,
    validate_gprop,
    validate_resolution,
    validate_timeframe,
)


# ── Session Tests ───────────────────────────────────────────────────────

class TestSessionConfig:
    def test_defaults(self):
        cfg = SessionConfig()
        assert cfg.hl == "en-US"
        assert cfg.tz == 360
        assert cfg.geo == ""
        assert cfg.timeout == (2, 5)
        assert cfg.proxies == ""
        assert cfg.retries == 0
        assert cfg.backoff_factor == 0
        assert cfg.requests_args is None

    def test_to_dict(self):
        cfg = SessionConfig(hl="es-ES", tz=120)
        d = cfg.to_dict()
        assert d["hl"] == "es-ES"
        assert d["tz"] == 120
        assert d["timeout"] == [2, 5]
        assert isinstance(d, dict)

    def test_from_dict(self):
        d = {"hl": "fr-FR", "tz": 0, "timeout": [5, 10]}
        cfg = SessionConfig.from_dict(d)
        assert cfg.hl == "fr-FR"
        assert cfg.tz == 0
        assert cfg.timeout == (5, 10)

    def test_from_dict_ignores_unknown_keys(self):
        d = {"hl": "en-US", "unknown_key": "value"}
        cfg = SessionConfig.from_dict(d)
        assert cfg.hl == "en-US"

    def test_roundtrip(self):
        original = SessionConfig(hl="de-DE", tz=60, retries=3)
        d = original.to_dict()
        restored = SessionConfig.from_dict(d)
        assert restored.hl == original.hl
        assert restored.tz == original.tz
        assert restored.retries == original.retries


class TestPayloadConfig:
    def test_to_dict(self):
        pc = PayloadConfig(kw_list=["python"], cat=0, timeframe="today 5-y", geo="US", gprop="")
        d = pc.to_dict()
        assert d["kw_list"] == ["python"]
        assert d["geo"] == "US"
        assert d["timeframe"] == "today 5-y"

    def test_defaults(self):
        pc = PayloadConfig()
        assert pc.kw_list == []
        assert pc.cat == 0
        assert pc.gprop == ""


class TestSession:
    @patch("cli_anything.pytrends.core.session.TrendReq")
    def test_client_creation(self, mock_trendreq):
        s = Session()
        client = s.client
        mock_trendreq.assert_called_once()
        assert client is not None

    @patch("cli_anything.pytrends.core.session.TrendReq")
    def test_client_cached(self, mock_trendreq):
        s = Session()
        c1 = s.client
        c2 = s.client
        assert c1 is c2
        assert mock_trendreq.call_count == 1

    @patch("cli_anything.pytrends.core.session.TrendReq")
    def test_reinit_clears_client(self, mock_trendreq):
        s = Session()
        _ = s.client
        s.reinit(hl="es-ES")
        assert s._client is None
        assert s._payload is None
        assert s.config.hl == "es-ES"

    @patch("cli_anything.pytrends.core.session.TrendReq")
    def test_build_payload(self, mock_trendreq):
        mock_instance = MagicMock()
        mock_trendreq.return_value = mock_instance
        s = Session()
        s.build_payload(kw_list=["python"], cat=0, timeframe="today 5-y", geo="US")
        assert s.payload is not None
        assert s.payload.kw_list == ["python"]
        assert s.payload.geo == "US"
        mock_instance.build_payload.assert_called_once()

    @patch("cli_anything.pytrends.core.session.TrendReq")
    def test_get_status_no_payload(self, mock_trendreq):
        s = Session()
        status = s.get_status()
        assert "config" in status
        assert "initialized" in status
        assert "payload" not in status

    @patch("cli_anything.pytrends.core.session.TrendReq")
    def test_get_status_with_payload(self, mock_trendreq):
        mock_trendreq.return_value = MagicMock()
        s = Session()
        s.build_payload(kw_list=["test"])
        status = s.get_status()
        assert "payload" in status
        assert status["payload"]["kw_list"] == ["test"]


# ── Formatting Tests ────────────────────────────────────────────────────

class TestFormatting:
    def test_df_to_json_with_data(self):
        df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        result = json.loads(df_to_json(df))
        assert result["rows"] == 2
        assert "data" in result

    def test_df_to_json_empty(self):
        df = pd.DataFrame()
        result = json.loads(df_to_json(df))
        assert result["rows"] == 0
        assert result["data"] == []

    def test_series_to_json(self):
        s = pd.Series(["a", "b", "c"])
        result = json.loads(series_to_json(s))
        assert result["rows"] == 3
        assert result["data"] == ["a", "b", "c"]

    def test_series_to_json_empty(self):
        s = pd.Series(dtype=object)
        result = json.loads(series_to_json(s))
        assert result["rows"] == 0

    def test_dict_to_json(self):
        data = {
            "python": {
                "top": pd.DataFrame({"query": ["a"], "value": [100]}),
                "rising": None,
            }
        }
        result = json.loads(dict_to_json(data))
        assert "python" in result
        assert result["python"]["top"] is not None
        assert result["python"]["rising"] is None

    def test_dict_to_json_plain(self):
        data = {"config": {"hl": "en-US", "tz": 360}, "initialized": False}
        result = json.loads(dict_to_json(data))
        assert result["config"]["hl"] == "en-US"
        assert result["initialized"] is False

    def test_list_to_json(self):
        data = [{"mid": "/m/1", "title": "Python"}]
        result = json.loads(list_to_json(data))
        assert result["count"] == 1
        assert result["data"][0]["title"] == "Python"

    def test_format_output_table_dataframe(self):
        df = pd.DataFrame({"a": [1, 2]})
        out = format_output(df, "table")
        assert "a" in out
        assert "1" in out

    def test_format_output_table_empty(self):
        df = pd.DataFrame()
        out = format_output(df, "table")
        assert out == "(no data)"

    def test_format_output_json_dataframe(self):
        df = pd.DataFrame({"x": [10]})
        out = format_output(df, "json")
        parsed = json.loads(out)
        assert parsed["rows"] == 1

    def test_format_output_csv_dataframe(self):
        df = pd.DataFrame({"col": [1, 2, 3]})
        out = format_output(df, "csv")
        assert "col" in out
        assert "1" in out

    def test_format_output_table_list(self):
        data = [{"a": 1, "b": 2}]
        out = format_output(data, "table")
        assert "1" in out

    def test_format_output_table_empty_list(self):
        out = format_output([], "table")
        assert out == "(no data)"

    def test_format_output_json_list(self):
        out = format_output([1, 2], "json")
        parsed = json.loads(out)
        assert parsed["count"] == 2

    def test_format_output_table_dict(self):
        data = {"kw": {"top": pd.DataFrame({"q": [1]}), "rising": None}}
        out = format_output(data, "table")
        assert "kw" in out
        assert "top" in out

    def test_format_output_csv_dict(self):
        data = {"kw": {"top": pd.DataFrame({"q": [1]}), "rising": None}}
        out = format_output(data, "csv")
        assert "# kw" in out


# ── Validator Tests ─────────────────────────────────────────────────────

class TestValidators:
    @pytest.mark.parametrize("gprop", ["", "images", "news", "youtube", "froogle"])
    def test_validate_gprop_valid(self, gprop):
        assert validate_gprop(gprop) == gprop

    def test_validate_gprop_invalid(self):
        with pytest.raises(ValueError, match="Invalid gprop"):
            validate_gprop("invalid")

    @pytest.mark.parametrize("res", ["COUNTRY", "REGION", "DMA", "CITY"])
    def test_validate_resolution_valid(self, res):
        assert validate_resolution(res) == res

    def test_validate_resolution_case_insensitive(self):
        assert validate_resolution("country") == "COUNTRY"

    def test_validate_resolution_invalid(self):
        with pytest.raises(ValueError, match="Invalid resolution"):
            validate_resolution("INVALID")

    @pytest.mark.parametrize(
        "tf",
        [
            "today 5-y",
            "today 3-m",
            "today 7-d",
            "now 1-d",
            "now 4-H",
            "2023-01-01 2023-12-31",
            "all",
        ],
    )
    def test_validate_timeframe_valid(self, tf):
        assert validate_timeframe(tf) == tf

    def test_validate_timeframe_invalid(self):
        with pytest.raises(ValueError, match="Invalid timeframe"):
            validate_timeframe("last week")

    def test_parse_keywords_single(self):
        assert parse_keywords("python") == ["python"]

    def test_parse_keywords_multiple(self):
        assert parse_keywords("python, javascript, rust") == ["python", "javascript", "rust"]

    def test_parse_keywords_whitespace(self):
        assert parse_keywords("  python  ,  javascript  ") == ["python", "javascript"]

    def test_parse_keywords_empty(self):
        with pytest.raises(ValueError, match="At least one keyword"):
            parse_keywords("")

    def test_parse_keywords_too_many(self):
        with pytest.raises(ValueError, match="maximum of 5"):
            parse_keywords("a,b,c,d,e,f")


# ── Core Function Error Tests ──────────────────────────────────────────

class TestCoreFunctions:
    def test_interest_over_time_no_payload(self):
        from cli_anything.pytrends.core.search import interest_over_time
        s = Session.__new__(Session)
        s._payload = None
        with pytest.raises(RuntimeError, match="No payload configured"):
            interest_over_time(s)

    def test_interest_by_region_no_payload(self):
        from cli_anything.pytrends.core.search import interest_by_region
        s = Session.__new__(Session)
        s._payload = None
        with pytest.raises(RuntimeError, match="No payload configured"):
            interest_by_region(s)

    def test_related_topics_no_payload(self):
        from cli_anything.pytrends.core.related import related_topics
        s = Session.__new__(Session)
        s._payload = None
        with pytest.raises(RuntimeError, match="No payload configured"):
            related_topics(s)

    def test_related_queries_no_payload(self):
        from cli_anything.pytrends.core.related import related_queries
        s = Session.__new__(Session)
        s._payload = None
        with pytest.raises(RuntimeError, match="No payload configured"):
            related_queries(s)
