import threading
import time
from collections import OrderedDict

from redis import Redis


class RateLimiter:
    def __init__(self, redis_url=""):
        self.redis = (
            Redis.from_url(redis_url, socket_connect_timeout=1, socket_timeout=1) if redis_url else None
        )
        self.buckets = OrderedDict()
        self.lock = threading.Lock()

    def allow(self, key, limit):
        minute = int(time.time()) // 60
        if self.redis:
            return (
                self.redis.eval(
                    "local n=redis.call('INCR',KEYS[1]); if n==1 then redis.call('EXPIRE',KEYS[1],120) end; return n",
                    1,
                    f"sentinel:rate:{key}:{minute}",
                )
                <= limit
            )
        with self.lock:
            old_minute, count = self.buckets.pop(key, (minute, 0))
            count = count + 1 if old_minute == minute else 1
            self.buckets[key] = (minute, count)
            if len(self.buckets) > 10000:
                self.buckets.popitem(last=False)
            return count <= limit
