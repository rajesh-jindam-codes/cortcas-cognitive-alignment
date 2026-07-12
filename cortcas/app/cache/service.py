import time
import json
import logging
from typing import Optional, Any
import redis
from app.core.config import settings

logger = logging.getLogger("cortcas.cache")

class CacheService:
    def __init__(self):
        self.redis_client = None
        self.use_redis = False
        
        # In-memory fallback cache
        self._in_memory_cache = {}  # format: {key: (value_str, expiry_timestamp)}
        
        # Test connection to Redis
        try:
            self.redis_client = redis.from_url(settings.REDIS_URL, socket_timeout=2.0)
            # Test ping
            self.redis_client.ping()
            self.use_redis = True
            logger.info("Successfully connected to Redis cache.")
        except Exception as e:
            logger.warning(f"Redis is unreachable ({e}). Falling back to In-Memory TTL Cache.")
            self.use_redis = False

    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from cache. Returns deserialized JSON or None."""
        if self.use_redis:
            try:
                val = self.redis_client.get(key)
                if val:
                    return json.loads(val.decode("utf-8"))
            except Exception as e:
                logger.error(f"Redis get error: {e}")
        else:
            # In-memory lookup
            item = self._in_memory_cache.get(key)
            if item:
                val_str, expiry = item
                if expiry is None or expiry > time.time():
                    return json.loads(val_str)
                else:
                    # Expired, clean it up
                    self._in_memory_cache.pop(key, None)
        return None

    def set(self, key: str, value: Any, ttl: int = 120) -> bool:
        """Store a JSON-serializable value in the cache with a Time-To-Live (TTL) in seconds."""
        val_str = json.dumps(value)
        if self.use_redis:
            try:
                return bool(self.redis_client.setex(key, ttl, val_str))
            except Exception as e:
                logger.error(f"Redis set error: {e}")
                return False
        else:
            # In-memory store
            expiry = time.time() + ttl if ttl else None
            self._in_memory_cache[key] = (val_str, expiry)
            return True

    def delete(self, key: str) -> bool:
        """Delete a key from cache."""
        if self.use_redis:
            try:
                return bool(self.redis_client.delete(key))
            except Exception as e:
                logger.error(f"Redis delete error: {e}")
                return False
        else:
            if key in self._in_memory_cache:
                del self._in_memory_cache[key]
                return True
            return False

    def invalidate_prefix(self, prefix: str) -> int:
        """Invalidate all keys matching the prefix."""
        count = 0
        if self.use_redis:
            try:
                keys = self.redis_client.keys(f"{prefix}*")
                if keys:
                    count = self.redis_client.delete(*keys)
                return count
            except Exception as e:
                logger.error(f"Redis invalidate error: {e}")
                return 0
        else:
            # In-memory prefix scan
            to_delete = [k for k in self._in_memory_cache.keys() if k.startswith(prefix)]
            for k in to_delete:
                self._in_memory_cache.pop(k, None)
                count += 1
            return count

    def flush_all(self) -> bool:
        """Flush all cache items."""
        if self.use_redis:
            try:
                self.redis_client.flushdb()
                return True
            except Exception as e:
                logger.error(f"Redis flush error: {e}")
                return False
        else:
            self._in_memory_cache.clear()
            return True
