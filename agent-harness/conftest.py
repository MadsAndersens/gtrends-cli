"""Root conftest for cli-anything-pytrends.

Ensures the real pytrends package is importable before test collection
by pre-importing it (prevents namespace shadowing by pytest's path manipulation).
"""

import pytrends.request  # noqa: F401 - force early import
