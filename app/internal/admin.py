import json

from fastapi import APIRouter, Depends

from app.models.redis import RedisClient

router = APIRouter()


@router.post("/context-unit-cleanup")
async def context_unit_cleanup(
    redis_client: RedisClient = Depends(RedisClient),
    context: str = "u_1234",
):
    redis_conn = redis_client.get_conn()
    redis_conn.delete(context)
    return "Clean up done"


@router.post("/all-context-cleanup")
async def all_context_cleanup(
    redis_client: RedisClient = Depends(RedisClient),
):
    redis_conn = redis_client.get_conn()
    redis_conn.flushdb()
    return "Clean up done"


@router.get("/get-context-message")
async def get_context_message(
    redis_client: RedisClient = Depends(RedisClient),
    context: str = "u_1234",
):
    redis_conn = redis_client.get_conn()
    return [json.loads(message) for message in redis_conn.lrange(context, 0, -1)]


@router.get("/get-context-list")
async def get_context_list(
    redis_client: RedisClient = Depends(RedisClient),
):
    # This is not good code, change it to scan
    redis_conn = redis_client.get_conn()
    return redis_conn.keys("*")
