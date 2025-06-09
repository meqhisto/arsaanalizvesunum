"""
Caching utilities for improved application performance
"""

import os
import json
import time
import hashlib
from functools import wraps
from typing import Any, Optional, Callable
from flask import current_app


class SimpleCache:
    """Simple in-memory cache implementation"""
    
    def __init__(self, default_timeout=300):
        self._cache = {}
        self.default_timeout = default_timeout
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired"""
        if key in self._cache:
            value, timestamp, timeout = self._cache[key]
            if time.time() - timestamp < timeout:
                return value
            else:
                del self._cache[key]
        return None
    
    def set(self, key: str, value: Any, timeout: Optional[int] = None) -> None:
        """Set value in cache with timeout"""
        if timeout is None:
            timeout = self.default_timeout
        
        self._cache[key] = (value, time.time(), timeout)
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    def clear(self) -> None:
        """Clear all cache entries"""
        self._cache.clear()
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        total_entries = len(self._cache)
        expired_entries = 0
        current_time = time.time()
        
        for key, (value, timestamp, timeout) in self._cache.items():
            if current_time - timestamp >= timeout:
                expired_entries += 1
        
        return {
            'total_entries': total_entries,
            'expired_entries': expired_entries,
            'active_entries': total_entries - expired_entries
        }


class RedisCache:
    """Redis cache implementation (if Redis is available)"""
    
    def __init__(self, redis_url=None, default_timeout=300):
        self.default_timeout = default_timeout
        self.redis_client = None
        
        try:
            import redis
            redis_url = redis_url or os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
            self.redis_client = redis.from_url(redis_url)
            # Test connection
            self.redis_client.ping()
        except (ImportError, Exception) as e:
            current_app.logger.warning(f"Redis not available, falling back to simple cache: {e}")
            self.redis_client = None
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from Redis cache"""
        if not self.redis_client:
            return None
        
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value.decode('utf-8'))
        except Exception as e:
            current_app.logger.error(f"Redis get error: {e}")
        
        return None
    
    def set(self, key: str, value: Any, timeout: Optional[int] = None) -> None:
        """Set value in Redis cache"""
        if not self.redis_client:
            return
        
        try:
            timeout = timeout or self.default_timeout
            serialized_value = json.dumps(value, default=str)
            self.redis_client.setex(key, timeout, serialized_value)
        except Exception as e:
            current_app.logger.error(f"Redis set error: {e}")
    
    def delete(self, key: str) -> bool:
        """Delete key from Redis cache"""
        if not self.redis_client:
            return False
        
        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            current_app.logger.error(f"Redis delete error: {e}")
            return False
    
    def clear(self) -> None:
        """Clear all cache entries"""
        if not self.redis_client:
            return
        
        try:
            self.redis_client.flushdb()
        except Exception as e:
            current_app.logger.error(f"Redis clear error: {e}")


class CacheManager:
    """Main cache manager that chooses between Redis and simple cache"""
    
    def __init__(self, app=None):
        self.app = app
        self._cache = None
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize cache with Flask app"""
        self.app = app
        
        # Try Redis first, fall back to simple cache
        redis_url = os.environ.get('REDIS_URL')
        if redis_url:
            self._cache = RedisCache(redis_url)
            app.logger.info("Using Redis cache")
        else:
            self._cache = SimpleCache()
            app.logger.info("Using simple in-memory cache")
        
        # Store cache manager in app extensions
        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['cache'] = self
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        return self._cache.get(key) if self._cache else None
    
    def set(self, key: str, value: Any, timeout: Optional[int] = None) -> None:
        """Set value in cache"""
        if self._cache:
            self._cache.set(key, value, timeout)
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        return self._cache.delete(key) if self._cache else False
    
    def clear(self) -> None:
        """Clear all cache entries"""
        if self._cache:
            self._cache.clear()


# Global cache instance
cache = CacheManager()


def cached(timeout=300, key_prefix=''):
    """Decorator for caching function results"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            key_parts = [key_prefix, func.__name__]
            
            # Add args to key
            for arg in args:
                if hasattr(arg, 'id'):
                    key_parts.append(str(arg.id))
                else:
                    key_parts.append(str(arg))
            
            # Add kwargs to key
            for k, v in sorted(kwargs.items()):
                key_parts.append(f"{k}:{v}")
            
            cache_key = hashlib.md5(':'.join(key_parts).encode()).hexdigest()
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            
            return result
        
        return wrapper
    return decorator


def cache_key(*args, **kwargs) -> str:
    """Generate cache key from arguments"""
    key_parts = []
    
    for arg in args:
        if hasattr(arg, 'id'):
            key_parts.append(str(arg.id))
        else:
            key_parts.append(str(arg))
    
    for k, v in sorted(kwargs.items()):
        key_parts.append(f"{k}:{v}")
    
    return hashlib.md5(':'.join(key_parts).encode()).hexdigest()


def invalidate_cache_pattern(pattern: str) -> int:
    """Invalidate cache keys matching pattern (Redis only)"""
    if hasattr(cache._cache, 'redis_client') and cache._cache.redis_client:
        try:
            keys = cache._cache.redis_client.keys(pattern)
            if keys:
                return cache._cache.redis_client.delete(*keys)
        except Exception as e:
            current_app.logger.error(f"Cache invalidation error: {e}")
    
    return 0


# Specific cache functions for common use cases
@cached(timeout=600, key_prefix='dashboard_stats')
def get_cached_dashboard_stats(user_id: int, office_id: Optional[int] = None):
    """Get cached dashboard statistics"""
    from utils.query_optimizer import QueryOptimizer
    return QueryOptimizer.get_dashboard_stats(user_id, office_id)


@cached(timeout=300, key_prefix='user_analyses')
def get_cached_user_analyses(user_id: int, limit: int = 10):
    """Get cached user analyses"""
    from utils.query_optimizer import QueryOptimizer
    return QueryOptimizer.get_analyses_with_user_and_office(user_id, limit)


@cached(timeout=300, key_prefix='user_contacts')
def get_cached_user_contacts(user_id: int, limit: int = 10):
    """Get cached user contacts"""
    from utils.query_optimizer import QueryOptimizer
    return QueryOptimizer.get_contacts_with_relationships(user_id, limit=limit)


@cached(timeout=180, key_prefix='recent_activities')
def get_cached_recent_activities(user_id: int, office_id: Optional[int] = None, limit: int = 10):
    """Get cached recent activities"""
    from utils.query_optimizer import QueryOptimizer
    return QueryOptimizer.get_recent_activities(user_id, office_id, limit)


def invalidate_user_cache(user_id: int):
    """Invalidate all cache entries for a specific user"""
    patterns = [
        f"dashboard_stats:*:{user_id}:*",
        f"user_analyses:*:{user_id}:*",
        f"user_contacts:*:{user_id}:*",
        f"recent_activities:*:{user_id}:*"
    ]
    
    total_invalidated = 0
    for pattern in patterns:
        total_invalidated += invalidate_cache_pattern(pattern)
    
    return total_invalidated


def invalidate_office_cache(office_id: int):
    """Invalidate all cache entries for a specific office"""
    patterns = [
        f"dashboard_stats:*:*:{office_id}",
        f"recent_activities:*:*:{office_id}:*"
    ]
    
    total_invalidated = 0
    for pattern in patterns:
        total_invalidated += invalidate_cache_pattern(pattern)
    
    return total_invalidated


# Cache warming functions
def warm_user_cache(user_id: int, office_id: Optional[int] = None):
    """Pre-warm cache for a user"""
    try:
        get_cached_dashboard_stats(user_id, office_id)
        get_cached_user_analyses(user_id)
        get_cached_user_contacts(user_id)
        get_cached_recent_activities(user_id, office_id)
        return True
    except Exception as e:
        current_app.logger.error(f"Cache warming error for user {user_id}: {e}")
        return False


def get_cache_stats() -> dict:
    """Get cache statistics"""
    if hasattr(cache._cache, 'get_stats'):
        return cache._cache.get_stats()
    else:
        return {'type': 'redis', 'status': 'connected' if cache._cache.redis_client else 'disconnected'}
