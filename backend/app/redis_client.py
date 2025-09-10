import redis
import os

REDIS_URL = os.getenv("REDISCLOUD_URL")

# Handle missing Redis URL gracefully
if REDIS_URL:
    try:
        r = redis.Redis.from_url(REDIS_URL)
        # Test the connection
        r.ping()
    except Exception as e:
        print(f"Redis connection failed: {e}")
        r = None
else:
    print("REDISCLOUD_URL not set, Redis disabled")
    r = None
