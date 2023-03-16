import json
import openai

from enum import Enum
from fastapi import APIRouter, Security, HTTPException, Depends
from fastapi.security import APIKeyHeader
from openai.error import AuthenticationError, RateLimitError
from pydantic import BaseModel
from starlette import status
from starlette.responses import Response

from app.models.redis import RedisClient

API_KEY_NAME = "X-API-KEY"
router = APIRouter()


class Message(BaseModel):
    role: str = "user"
    content: str


class Model(Enum):
    GPT_3_5_TURBO = "gpt-3.5-turbo"
    TEXT_DAVINCI_003 = "text-davinci-003"
    DAVINCI = "davinci"
    CURIE = "curie"
    BABBAGE = "babbage"
    ADA = "ada"


@router.get("/models")
async def models(api_key: str = Security(APIKeyHeader(name=API_KEY_NAME, auto_error=True))):
    openai.api_key = api_key

    return await openai.Model.alist()


@router.post("/chat")
async def chat(
    message: Message,
    model: Model = Model.GPT_3_5_TURBO,
    max_tokens: int = 2048,
    presence_penalty: float = 0.5,
    frequency_penalty: float = 0.5,
    api_key: str = Security(APIKeyHeader(name=API_KEY_NAME, auto_error=True)),
    redis_client: RedisClient = Depends(RedisClient),
    user_id: str = "u_1234",
):
    openai.api_key = api_key

    # Cache messages
    redis_conn = redis_client.get_conn()
    redis_conn.rpush(user_id, json.dumps(message.__dict__))
    messages = [json.loads(message) for message in redis_conn.lrange(user_id, 0, 10)]

    # https://platform.openai.com/docs/api-reference/completions/create
    while True:
        try:
            result = openai.ChatCompletion.create(
                model=model.value,
                max_tokens=max_tokens,
                presence_penalty=presence_penalty,
                frequency_penalty=frequency_penalty,
                messages=messages,
            )

        except AuthenticationError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except RateLimitError as e:
            print(e)
            continue
        break

    try:
        resp = result.get("choices")[0].get("message")
        # cache the response
        redis_conn.rpush(user_id, json.dumps(Message(role=resp.get("role"), content=resp.get("content")).__dict__))
        # Keep only the last 10 messages
        redis_conn.ltrim(user_id, 0, 9)
        # Sending results messages
        return Response(resp.get("content"))
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=e)
