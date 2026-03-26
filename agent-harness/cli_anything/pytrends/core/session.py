"""Session management for pytrends CLI harness.

Wraps TrendReq instantiation and lifecycle, providing a stateful session
that persists configuration across commands in REPL mode.
"""

from dataclasses import dataclass, field
from typing import Optional

from pytrends.request import TrendReq


@dataclass
class SessionConfig:
    """Configuration for a pytrends session."""

    hl: str = "en-US"
    tz: int = 360
    geo: str = ""
    timeout: tuple = (2, 5)
    proxies: str = ""
    retries: int = 0
    backoff_factor: float = 0
    requests_args: Optional[dict] = None

    def to_dict(self) -> dict:
        return {
            "hl": self.hl,
            "tz": self.tz,
            "geo": self.geo,
            "timeout": list(self.timeout),
            "proxies": self.proxies,
            "retries": self.retries,
            "backoff_factor": self.backoff_factor,
            "requests_args": self.requests_args,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SessionConfig":
        data = dict(data)
        if "timeout" in data and isinstance(data["timeout"], list):
            data["timeout"] = tuple(data["timeout"])
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class PayloadConfig:
    """Configuration for the current search payload."""

    kw_list: list = field(default_factory=list)
    cat: int = 0
    timeframe: str = "today 5-y"
    geo: str = ""
    gprop: str = ""

    def to_dict(self) -> dict:
        return {
            "kw_list": self.kw_list,
            "cat": self.cat,
            "timeframe": self.timeframe,
            "geo": self.geo,
            "gprop": self.gprop,
        }


class Session:
    """Manages a pytrends TrendReq session with persistent state."""

    def __init__(self, config: Optional[SessionConfig] = None):
        self.config = config or SessionConfig()
        self._client: Optional[TrendReq] = None
        self._payload: Optional[PayloadConfig] = None

    @property
    def client(self) -> TrendReq:
        if self._client is None:
            self._client = self._create_client()
        return self._client

    @property
    def payload(self) -> Optional[PayloadConfig]:
        return self._payload

    def _create_client(self) -> TrendReq:
        return TrendReq(
            hl=self.config.hl,
            tz=self.config.tz,
            geo=self.config.geo,
            timeout=self.config.timeout,
            proxies=self.config.proxies,
            retries=self.config.retries,
            backoff_factor=self.config.backoff_factor,
            requests_args=self.config.requests_args,
        )

    def reinit(self, **kwargs):
        """Re-initialize the session with updated config values."""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        self._client = None
        self._payload = None

    def build_payload(self, kw_list, cat=0, timeframe="today 5-y", geo="", gprop=""):
        """Build a search payload and store it in session state."""
        self._payload = PayloadConfig(
            kw_list=kw_list,
            cat=cat,
            timeframe=timeframe,
            geo=geo,
            gprop=gprop,
        )
        self.client.build_payload(
            kw_list=kw_list,
            cat=cat,
            timeframe=timeframe,
            geo=geo,
            gprop=gprop,
        )

    def get_status(self) -> dict:
        """Return current session status as a dict."""
        status = {
            "config": self.config.to_dict(),
            "initialized": self._client is not None,
        }
        if self._payload:
            status["payload"] = self._payload.to_dict()
        return status
