import time
from typing import Dict, Tuple, Any, Optional

class SimpleCache:
    """
    In-memory cache with TTL. 
    Not for production persistence — replace with Redis/Memcached in a scaled environment.
    """
    def __init__(self, ttl_seconds: int = 300):
        # Store: key -> (timestamp, value)
        self._store: Dict[str, Tuple[float, Any]] = {}
        self._ttl = ttl_seconds

    def get(self, key: str) -> Optional[Any]:
        if key in self._store:
            ts, value = self._store[key]
            if time.time() - ts < self._ttl:
                return value
            else:
                # Expired
                del self._store[key]
        return None

    def set(self, key: str, value: Any):
        self._store[key] = (time.time(), value)

# Global cache instance (default 5 min TTL)
data_cache = SimpleCache(ttl_seconds=300)
