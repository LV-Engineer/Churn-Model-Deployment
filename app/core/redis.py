from redis import Redis

from app.core.settings import settings

redis_client = Redis.from_url(settings.redis_url)