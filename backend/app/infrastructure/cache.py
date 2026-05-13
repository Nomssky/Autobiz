"""
Redis Cache Layer for AutoBiz Engine
Provides caching utilities to reduce database load and improve response times.
"""
import json
import logging
import hashlib
from functools import wraps
from typing import Any, Optional, Callable, TypeVar, ParamSpec
from datetime import timedelta

from redis import Redis
from app.config import settings

logger = logging.getLogger(__name__)

# Global Redis client (lazy-initialized)
_redis_client: Optional[Redis] = None


def get_redis() -> Redis:
    """Get or create the Redis client singleton."""
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = Redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                max_connections=20,
            )
            _redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.warning(f"Redis unavailable: {e}. Caching disabled.")
            _redis_client = None
    return _redis_client


def _make_cache_key(prefix: str, *args, **kwargs) -> str:
    """Generate a deterministic cache key from prefix and arguments."""
    key_parts = [prefix]
    for arg in args:
        key_parts.append(str(arg))
    if kwargs:
        key_parts.append(
            hashlib.md5(json.dumps(kwargs, sort_keys=True, default=str).encode()).hexdigest()
        )
    return ":".join(key_parts)


F = TypeVar("F", bound=Callable)
P = ParamSpec("P")


def cache_result(
    prefix: str = "cache",
    ttl: int = 300,
    skip_cache: bool = False,
) -> Callable[[F], F]:
    """
    Decorator that caches function results in Redis.

    Args:
        prefix: Cache key prefix (e.g., "business_metrics").
        ttl: Time-to-live in seconds (default: 300 = 5 minutes).
        skip_cache: If True, always call the function and update cache.

    Usage:
        @cache_result(prefix="business_metrics", ttl=600)
        def get_business_metrics(business_id: str) -> dict:
            ...
    """
    def decorator(func: F) -> F:
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
            redis = get_redis()
            if redis is None or skip_cache:
                return func(*args, **kwargs)

            cache_key = _make_cache_key(prefix, *args, **kwargs)
            try:
                # Try to get cached value
                cached = redis.get(cache_key)
                if cached is not None:
                    logger.debug(f"Cache HIT: {cache_key}")
                    return json.loads(cached)

                # Call the actual function
                result = func(*args, **kwargs)

                # Serialize and store in cache
                redis.setex(
                    cache_key,
                    timedelta(seconds=ttl),
                    json.dumps(result, default=str),
                )
                logger.debug(f"Cache MISS → stored: {cache_key}")
                return result

            except Exception as e:
                logger.warning(f"Cache error for key {cache_key}: {e}")
                return func(*args, **kwargs)

        wrapper.__name__ = func.__name__
        wrapper.__wrapped__ = func  # type: ignore
        return wrapper  # type: ignore
    return decorator


def invalidate_cache(prefix: str, *args: Any, **kwargs: Any) -> int:
    """
    Invalidate all cache keys matching a pattern.

    Args:
        prefix: The key prefix to match.
        *args: Additional key components to narrow the pattern.

    Returns:
        Number of keys deleted.
    """
    redis = get_redis()
    if redis is None:
        return 0

    pattern = _make_cache_key(prefix, *args, **kwargs)
    if args or kwargs:
        pattern += "*"
    else:
        pattern += ":*"

    try:
        keys = redis.keys(pattern)
        if keys:
            deleted = redis.delete(*keys)
            logger.info(f"Invalidated {deleted} cache keys matching: {pattern}")
            return deleted
    except Exception as e:
        logger.warning(f"Cache invalidation error: {e}")
    return 0


class RateLimiter:
    """Simple sliding-window rate limiter using Redis."""

    def __init__(self, redis_client: Optional[Redis] = None):
        self.redis = redis_client or get_redis()

    def is_allowed(
        self,
        key: str,
        max_requests: int = 100,
        window_seconds: int = 60,
    ) -> bool:
        """
        Check if a request is allowed under the rate limit.

        Args:
            key: Unique identifier (e.g., user ID or IP).
            max_requests: Maximum requests allowed in the window.
            window_seconds: Time window in seconds.

        Returns:
            True if the request is allowed, False otherwise.
        """
        if self.redis is None:
            return True  # No Redis = no rate limiting

        cache_key = f"rate_limit:{key}"
        try:
            pipe = self.redis.pipeline()
            now = int(1000)  # Current time in ms approximation
            pipe.zremrangebyscore(cache_key, 0, now - window_seconds * 1000)
            pipe.zcard(cache_key)
            pipe.zadd(cache_key, {str(now): now})
            pipe.expire(cache_key, window_seconds)
            _, count, _, _ = pipe.execute()

            return count < max_requests
        except Exception as e:
            logger.warning(f"Rate limiter error: {e}")
            return True


# Global rate limiter instances
api_rate_limiter = RateLimiter()