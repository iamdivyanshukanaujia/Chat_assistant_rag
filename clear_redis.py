"""
Clear all Redis cache
"""
from src.caching import CacheManager

print("Clearing Redis cache...")

# Initialize cache manager
cache = CacheManager()

# Clear all caches
cache.invalidate_all()

print("All caches cleared! Fresh start ready.")
