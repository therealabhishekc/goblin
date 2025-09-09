import redis
import os

REDIS_URL = os.getenv("REDISCLOUD_URL", "")
r = redis.Redis.from_url(REDIS_URL)
