import time
from collections import defaultdict
from typing import Dict, List, Tuple

class RateLimiter:
    """Simple sliding-window rate limiter per API source."""
    def __init__(self):
        self._calls: Dict[str, List[float]] = defaultdict(list)
        # Limits: (max_calls, window_seconds)
        self._limits: Dict[str, Tuple[int, int]] = {
            "finnhub": (60, 60),      # 60 calls per minute
            "fmp": (250, 86400),      # 250 calls per day
            "newsapi": (100, 86400),  # 100 calls per day
        }

    def can_call(self, source: str) -> bool:
        max_calls, window = self._limits.get(source, (100, 60))
        now = time.time()
        # Filter out timestamps older than the window
        self._calls[source] = [t for t in self._calls[source] if now - t < window]
        return len(self._calls[source]) < max_calls

    def record_call(self, source: str):
        self._calls[source].append(time.time())

rate_limiter = RateLimiter()
