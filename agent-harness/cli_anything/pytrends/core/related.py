"""Related topics and queries for pytrends CLI harness."""

from cli_anything.pytrends.core.cache import cached_call
from cli_anything.pytrends.core.session import Session


def related_topics(session: Session) -> dict:
    """Fetch related topics for the current payload.

    Returns a dict of {keyword: {'top': DataFrame|None, 'rising': DataFrame|None}}.
    """
    if session.payload is None:
        raise RuntimeError("No payload configured. Run a search command with keywords first.")
    return cached_call(
        session.cache,
        session.cache_ttl,
        "related.topics",
        session.cache_key_inputs(),
        lambda: session.client.related_topics(),
    )


def related_queries(session: Session) -> dict:
    """Fetch related queries for the current payload.

    Returns a dict of {keyword: {'top': DataFrame|None, 'rising': DataFrame|None}}.
    """
    if session.payload is None:
        raise RuntimeError("No payload configured. Run a search command with keywords first.")
    return cached_call(
        session.cache,
        session.cache_ttl,
        "related.queries",
        session.cache_key_inputs(),
        lambda: session.client.related_queries(),
    )
