import os

redis_host = os.environ.get("REDIS_HOST", "localhost")
redis_port = int(os.environ.get("REDIS_PORT", 6379))

MESSAGE_EXPIRE_TIME = 60 * 60 * 6