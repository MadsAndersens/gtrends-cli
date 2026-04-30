"""On-disk cache with TTL for pytrends CLI harness.

Caches the raw return values (DataFrame/Series/dict/list) of upstream
pytrends calls keyed by a hash of the request inputs. Cache hits skip
the network entirely, which is the main lever for surviving the
unofficial endpoint's rate limiting during agent loops.
"""

from __future__ import annotations

import hashlib
import json
import os
import pickle
import re
import sys
import time
from dataclasses import dataclass
from typing import Any, Callable, Optional


# ── Duration parsing ────────────────────────────────────────────────────

_DURATION_RE = re.compile(r"^\s*(\d+)\s*([smhd])\s*$", re.IGNORECASE)
_UNIT_SECONDS = {"s": 1, "m": 60, "h": 3600, "d": 86400}


def parse_duration(value: Optional[str]) -> Optional[float]:
    """Parse a TTL string like '1h', '30m', '7d', 'off' to seconds.

    Returns None when caching is disabled (value is None, '', 'off', '0').
    Raises ValueError for malformed input.
    """
    if value is None:
        return None
    s = str(value).strip().lower()
    if s in ("", "off", "none", "false", "0"):
        return None
    m = _DURATION_RE.match(s)
    if not m:
        raise ValueError(
            f"Invalid cache duration {value!r}. "
            "Use forms like '30s', '15m', '1h', '24h', '7d', or 'off'."
        )
    n, unit = m.groups()
    return int(n) * _UNIT_SECONDS[unit.lower()]


# ── Cache directory ─────────────────────────────────────────────────────

def default_cache_dir() -> str:
    """Return the platform-appropriate cache directory path."""
    env = os.environ.get("CLI_ANYTHING_PYTRENDS_CACHE_DIR")
    if env:
        return env
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~\\AppData\\Local")
        return os.path.join(base, "cli-anything-pytrends", "Cache")
    xdg = os.environ.get("XDG_CACHE_HOME")
    if xdg:
        return os.path.join(xdg, "cli-anything-pytrends")
    return os.path.expanduser("~/.cache/cli-anything-pytrends")


# ── DiskCache ───────────────────────────────────────────────────────────

@dataclass
class CacheEntry:
    value: Any
    command: str
    key_inputs: dict
    created_at: float
    ttl: float

    def is_expired(self, now: Optional[float] = None) -> bool:
        now = now if now is not None else time.time()
        return (now - self.created_at) > self.ttl


class DiskCache:
    """Simple per-file pickle cache with TTL and basic stats.

    Each entry lives at ``<cache_dir>/<sha256-hex>.pkl`` and stores a
    pickled :class:`CacheEntry`. Lookups verify the TTL on read; expired
    entries are deleted lazily.
    """

    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = cache_dir or default_cache_dir()

    def _ensure_dir(self) -> None:
        os.makedirs(self.cache_dir, exist_ok=True)

    @staticmethod
    def make_key(command: str, inputs: dict) -> str:
        """Hash (command, inputs) into a stable hex digest."""
        payload = {"command": command, "inputs": _normalize(inputs)}
        blob = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        return hashlib.sha256(blob).hexdigest()

    def _path(self, key: str) -> str:
        return os.path.join(self.cache_dir, f"{key}.pkl")

    def get(self, command: str, inputs: dict) -> Optional[Any]:
        """Return the cached value for (command, inputs) or None.

        Expired entries are deleted on access.
        """
        key = self.make_key(command, inputs)
        path = self._path(key)
        if not os.path.exists(path):
            return None
        try:
            with open(path, "rb") as f:
                entry: CacheEntry = pickle.load(f)
        except Exception:
            # Corrupt entry — remove and miss
            self._silent_unlink(path)
            return None
        if entry.is_expired():
            self._silent_unlink(path)
            return None
        return entry.value

    def set(self, command: str, inputs: dict, value: Any, ttl: float) -> None:
        """Store ``value`` for (command, inputs) with ``ttl`` seconds."""
        if ttl is None or ttl <= 0:
            return
        self._ensure_dir()
        key = self.make_key(command, inputs)
        entry = CacheEntry(
            value=value,
            command=command,
            key_inputs=_normalize(inputs),
            created_at=time.time(),
            ttl=ttl,
        )
        tmp = self._path(key) + ".tmp"
        with open(tmp, "wb") as f:
            pickle.dump(entry, f, protocol=pickle.HIGHEST_PROTOCOL)
        os.replace(tmp, self._path(key))

    def clear(self) -> int:
        """Delete every cache entry. Returns the number of files removed."""
        if not os.path.isdir(self.cache_dir):
            return 0
        removed = 0
        for name in os.listdir(self.cache_dir):
            if not name.endswith(".pkl"):
                continue
            if self._silent_unlink(os.path.join(self.cache_dir, name)):
                removed += 1
        return removed

    def stats(self) -> dict:
        """Summary of cache contents: counts, sizes, age, per-command breakdown."""
        result = {
            "cache_dir": self.cache_dir,
            "entries": 0,
            "expired": 0,
            "size_bytes": 0,
            "by_command": {},
            "oldest": None,
            "newest": None,
        }
        if not os.path.isdir(self.cache_dir):
            return result
        now = time.time()
        for name in os.listdir(self.cache_dir):
            if not name.endswith(".pkl"):
                continue
            path = os.path.join(self.cache_dir, name)
            try:
                size = os.path.getsize(path)
                with open(path, "rb") as f:
                    entry: CacheEntry = pickle.load(f)
            except Exception:
                continue
            result["entries"] += 1
            result["size_bytes"] += size
            if entry.is_expired(now):
                result["expired"] += 1
            cmd = entry.command
            cmd_stats = result["by_command"].setdefault(
                cmd, {"entries": 0, "size_bytes": 0}
            )
            cmd_stats["entries"] += 1
            cmd_stats["size_bytes"] += size
            if result["oldest"] is None or entry.created_at < result["oldest"]:
                result["oldest"] = entry.created_at
            if result["newest"] is None or entry.created_at > result["newest"]:
                result["newest"] = entry.created_at
        return result

    @staticmethod
    def _silent_unlink(path: str) -> bool:
        try:
            os.unlink(path)
            return True
        except OSError:
            return False


# ── Helpers ─────────────────────────────────────────────────────────────

def _normalize(value: Any) -> Any:
    """Recursively normalize cache-key inputs for stable hashing.

    Tuples → lists, sets → sorted lists, everything else passed through.
    """
    if isinstance(value, dict):
        return {k: _normalize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_normalize(v) for v in value]
    if isinstance(value, set):
        return sorted(_normalize(v) for v in value)
    return value


# ── Process-wide tracking for "_cached" output annotation ───────────────

_LAST_HIT: bool = False


def _record_hit(hit: bool) -> None:
    global _LAST_HIT
    _LAST_HIT = hit


def last_was_cache_hit() -> bool:
    """Whether the most recent ``cached_call`` returned a cached value."""
    return _LAST_HIT


def reset_hit_marker() -> None:
    global _LAST_HIT
    _LAST_HIT = False


# ── cached_call: the wrapper used by core/* functions ───────────────────

def cached_call(
    cache: Optional[DiskCache],
    ttl: Optional[float],
    command: str,
    inputs: dict,
    fetch: Callable[[], Any],
) -> Any:
    """Return a cached value for (command, inputs) or compute and cache it.

    ``cache`` and ``ttl`` may be None to bypass caching entirely (still
    invokes ``fetch``). Records hit/miss for the last call so the CLI
    can annotate output with ``_cached``.
    """
    if cache is None or ttl is None or ttl <= 0:
        _record_hit(False)
        return fetch()
    cached = cache.get(command, inputs)
    if cached is not None:
        _record_hit(True)
        return cached
    value = fetch()
    cache.set(command, inputs, value, ttl)
    _record_hit(False)
    return value
