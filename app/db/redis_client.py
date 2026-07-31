import redis
from app.core.config import settings

# Create a singleton Redis client
# decode_responses=True ensures we get strings back instead of bytes
redis_client = redis.from_url(
    settings.REDIS_URL, 
    decode_responses=True
)

def get_redis_client():
    return redis_client
