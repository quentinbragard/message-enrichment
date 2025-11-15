# utils/cache_helpers.py
"""
Cache helper utilities
"""
import hashlib
from typing import Any
import json


def generate_cache_key(*args) -> str:
    """Generate a cache key from arguments"""
    # Combine all arguments
    data = json.dumps(args, sort_keys=True, default=str)
    
    # Generate hash
    return hashlib.md5(data.encode()).hexdigest()


def parse_cache_ttl(ttl_str: str) -> int:
    """Parse cache TTL string to seconds"""
    if ttl_str.endswith('h'):
        return int(ttl_str[:-1]) * 3600
    elif ttl_str.endswith('m'):
        return int(ttl_str[:-1]) * 60
    elif ttl_str.endswith('s'):
        return int(ttl_str[:-1])
    else:
        return int(ttl_str)