import redis

from app.config.constants import redis_host, redis_port


class RedisClient:
    def __init__(self):
        self.pool = redis.ConnectionPool(
            host=redis_host, port=redis_port, db=0, encoding="utf-8", decode_responses=True
        )
        self._conn = redis.StrictRedis(connection_pool=self.pool)

    def get_conn(self):
        return self._conn
