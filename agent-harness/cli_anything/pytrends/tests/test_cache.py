"""Unit tests for the on-disk cache."""

import os
import time
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from cli_anything.pytrends.core.cache import (
    DiskCache,
    cached_call,
    last_was_cache_hit,
    parse_duration,
    reset_hit_marker,
)
from cli_anything.pytrends.core.session import Session


# ── parse_duration ──────────────────────────────────────────────────────

class TestParseDuration:
    @pytest.mark.parametrize("value,expected", [
        ("30s", 30),
        ("15m", 900),
        ("1h", 3600),
        ("24h", 86400),
        ("7d", 7 * 86400),
        (" 2H ", 2 * 3600),
    ])
    def test_valid(self, value, expected):
        assert parse_duration(value) == expected

    @pytest.mark.parametrize("value", [None, "", "off", "OFF", "0", "none", "false"])
    def test_disabled(self, value):
        assert parse_duration(value) is None

    @pytest.mark.parametrize("value", ["1", "abc", "1y", "h", "-5m", "1.5h"])
    def test_invalid(self, value):
        with pytest.raises(ValueError):
            parse_duration(value)


# ── DiskCache ───────────────────────────────────────────────────────────

class TestDiskCache:
    def test_make_key_stable(self, tmp_path):
        cache = DiskCache(str(tmp_path))
        k1 = cache.make_key("cmd", {"a": 1, "b": 2})
        k2 = cache.make_key("cmd", {"b": 2, "a": 1})
        assert k1 == k2

    def test_make_key_differs_on_inputs(self, tmp_path):
        cache = DiskCache(str(tmp_path))
        k1 = cache.make_key("cmd", {"a": 1})
        k2 = cache.make_key("cmd", {"a": 2})
        k3 = cache.make_key("other", {"a": 1})
        assert k1 != k2
        assert k1 != k3

    def test_make_key_normalizes_tuples(self, tmp_path):
        cache = DiskCache(str(tmp_path))
        k1 = cache.make_key("cmd", {"x": (1, 2)})
        k2 = cache.make_key("cmd", {"x": [1, 2]})
        assert k1 == k2

    def test_set_then_get_returns_value(self, tmp_path):
        cache = DiskCache(str(tmp_path))
        df = pd.DataFrame({"a": [1, 2, 3]})
        cache.set("c", {"k": "v"}, df, ttl=60)
        got = cache.get("c", {"k": "v"})
        assert isinstance(got, pd.DataFrame)
        assert got.equals(df)

    def test_get_miss_returns_none(self, tmp_path):
        cache = DiskCache(str(tmp_path))
        assert cache.get("c", {"k": "missing"}) is None

    def test_expired_entry_is_pruned(self, tmp_path):
        cache = DiskCache(str(tmp_path))
        cache.set("c", {"k": "v"}, "value", ttl=60)
        # Backdate creation time
        path = cache._path(cache.make_key("c", {"k": "v"}))
        old_mtime = time.time() - 120
        os.utime(path, (old_mtime, old_mtime))
        # Manually rewrite with ttl 1s to force expiry
        cache.set("c", {"k": "v"}, "value", ttl=1)
        time.sleep(1.1)
        assert cache.get("c", {"k": "v"}) is None
        # File should also be gone
        assert not os.path.exists(path)

    def test_set_with_zero_ttl_is_noop(self, tmp_path):
        cache = DiskCache(str(tmp_path))
        cache.set("c", {"k": "v"}, "value", ttl=0)
        cache.set("c", {"k": "v"}, "value", ttl=None)
        assert cache.get("c", {"k": "v"}) is None

    def test_clear_removes_all_entries(self, tmp_path):
        cache = DiskCache(str(tmp_path))
        cache.set("c", {"k": "v1"}, "a", ttl=60)
        cache.set("c", {"k": "v2"}, "b", ttl=60)
        removed = cache.clear()
        assert removed == 2
        assert cache.get("c", {"k": "v1"}) is None

    def test_clear_on_missing_dir(self, tmp_path):
        cache = DiskCache(str(tmp_path / "does-not-exist"))
        assert cache.clear() == 0

    def test_stats_breakdown(self, tmp_path):
        cache = DiskCache(str(tmp_path))
        cache.set("alpha", {"k": 1}, "x", ttl=60)
        cache.set("alpha", {"k": 2}, "y", ttl=60)
        cache.set("beta", {"k": 3}, "z", ttl=60)
        stats = cache.stats()
        assert stats["entries"] == 3
        assert stats["expired"] == 0
        assert stats["by_command"]["alpha"]["entries"] == 2
        assert stats["by_command"]["beta"]["entries"] == 1
        assert stats["size_bytes"] > 0
        assert stats["oldest"] is not None
        assert stats["newest"] >= stats["oldest"]

    def test_corrupt_entry_treated_as_miss(self, tmp_path):
        cache = DiskCache(str(tmp_path))
        os.makedirs(str(tmp_path), exist_ok=True)
        key = cache.make_key("c", {"k": "v"})
        with open(cache._path(key), "wb") as f:
            f.write(b"not a real pickle")
        assert cache.get("c", {"k": "v"}) is None
        # Corrupt file should have been cleaned up
        assert not os.path.exists(cache._path(key))


# ── cached_call ─────────────────────────────────────────────────────────

class TestCachedCall:
    def test_disabled_cache_calls_fetch(self, tmp_path):
        fetch = MagicMock(return_value="value")
        out = cached_call(None, None, "c", {"k": "v"}, fetch)
        assert out == "value"
        assert fetch.call_count == 1
        assert last_was_cache_hit() is False

    def test_miss_then_hit(self, tmp_path):
        cache = DiskCache(str(tmp_path))
        fetch = MagicMock(return_value="value")
        out1 = cached_call(cache, 60, "c", {"k": "v"}, fetch)
        assert last_was_cache_hit() is False
        out2 = cached_call(cache, 60, "c", {"k": "v"}, fetch)
        assert last_was_cache_hit() is True
        assert out1 == out2 == "value"
        assert fetch.call_count == 1

    def test_different_inputs_separate_entries(self, tmp_path):
        cache = DiskCache(str(tmp_path))
        fetch1 = MagicMock(return_value="a")
        fetch2 = MagicMock(return_value="b")
        cached_call(cache, 60, "c", {"k": 1}, fetch1)
        cached_call(cache, 60, "c", {"k": 2}, fetch2)
        assert fetch1.call_count == 1
        assert fetch2.call_count == 1

    def test_reset_hit_marker(self):
        reset_hit_marker()
        assert last_was_cache_hit() is False


# ── End-to-end integration with Session/core ────────────────────────────

class TestSessionCacheIntegration:
    def test_interest_over_time_caches(self, tmp_path):
        """Two consecutive calls should produce one network call."""
        from cli_anything.pytrends.core.search import interest_over_time

        df = pd.DataFrame({"python": [1, 2, 3]})
        with patch("cli_anything.pytrends.core.session.TrendReq") as mock_trendreq:
            mock_client = MagicMock()
            mock_client.interest_over_time.return_value = df
            mock_trendreq.return_value = mock_client

            s = Session()
            s.cache = DiskCache(str(tmp_path))
            s.cache_ttl = 60
            s.build_payload(kw_list=["python"], timeframe="today 5-y", geo="US")

            r1 = interest_over_time(s)
            assert last_was_cache_hit() is False
            r2 = interest_over_time(s)
            assert last_was_cache_hit() is True
            assert r1.equals(r2)
            # Network was hit exactly once
            assert mock_client.interest_over_time.call_count == 1

    def test_cache_off_always_hits_network(self, tmp_path):
        from cli_anything.pytrends.core.search import interest_over_time

        df = pd.DataFrame({"python": [1, 2, 3]})
        with patch("cli_anything.pytrends.core.session.TrendReq") as mock_trendreq:
            mock_client = MagicMock()
            mock_client.interest_over_time.return_value = df
            mock_trendreq.return_value = mock_client

            s = Session()
            s.cache = None
            s.cache_ttl = None
            s.build_payload(kw_list=["python"], timeframe="today 5-y", geo="US")

            interest_over_time(s)
            interest_over_time(s)
            assert mock_client.interest_over_time.call_count == 2

    def test_cache_key_includes_session_locale(self, tmp_path):
        """Switching hl/tz should miss the cache even with same payload."""
        from cli_anything.pytrends.core.search import interest_over_time

        df = pd.DataFrame({"python": [1]})
        with patch("cli_anything.pytrends.core.session.TrendReq") as mock_trendreq:
            mock_client = MagicMock()
            mock_client.interest_over_time.return_value = df
            mock_trendreq.return_value = mock_client

            cache = DiskCache(str(tmp_path))
            s1 = Session()
            s1.cache, s1.cache_ttl = cache, 60
            s1.config.hl = "en-US"
            s1.build_payload(kw_list=["python"], timeframe="today 5-y", geo="US")
            interest_over_time(s1)

            s2 = Session()
            s2.cache, s2.cache_ttl = cache, 60
            s2.config.hl = "es-ES"
            s2.build_payload(kw_list=["python"], timeframe="today 5-y", geo="US")
            interest_over_time(s2)

            assert mock_client.interest_over_time.call_count == 2
