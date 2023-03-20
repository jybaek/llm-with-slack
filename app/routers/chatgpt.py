import json
import logging
from enum import Enum

import backoff
import openai
from fastapi import APIRouter, Security, HTTPException
from fastapi.security import APIKeyHeader
from openai.error import AuthenticationError
from pydantic import BaseModel
from starlette import status
from starlette.responses import Response

from app.models.redis import RedisClient

API_KEY_NAME = "X-API-KEY"
router = APIRouter()

logging.getLogger('backoff').setLevel(logging.ERROR)


class Message(BaseModel):
    role: str = "user"
    content: str


class Model(Enum):
    GPT_3_5_TURBO = "gpt-3.5-turbo"


@router.get("/models")
async def models(api_key: str = Security(APIKeyHeader(name=API_KEY_NAME, auto_error=True))):
    openai.api_key = api_key

    return await openai.Model.alist()


@backoff.on_exception(backoff.expo, openai.error.RateLimitError, max_tries=3, max_time=10, jitter=None)
def completions_with_backoff(**kwargs):
    return openai.ChatCompletion.create(**kwargs)


@router.post("/chat")
async def chat(
    message: Message,
    model: Model = Model.GPT_3_5_TURBO,
    max_tokens: int = 2048,
    presence_penalty: float = 0.5,
    frequency_penalty: float = 0.5,
    api_key: str = Security(APIKeyHeader(name=API_KEY_NAME, auto_error=True)),
    user_id: str = "u_1234",
    number_of_messages_to_keep: int = 5,
):
    logging.info(f"request message: {message.__dict__}")
    openai.api_key = api_key

    # Cache messages
    if number_of_messages_to_keep:
        redis_conn = RedisClient().get_conn()
        redis_conn.rpush(user_id, json.dumps(message.__dict__))
        messages = [json.loads(message) for message in redis_conn.lrange(user_id, 0, number_of_messages_to_keep)]
    else:
        messages = [message.__dict__]

    # https://platform.openai.com/docs/api-reference/completions/create
    try:
        result = completions_with_backoff(
            model=model.value,
            max_tokens=max_tokens,
            presence_penalty=presence_penalty,
            frequency_penalty=frequency_penalty,
            messages=messages,
        )
    except AuthenticationError as e:
        logging.exception(e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logging.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    try:
        resp = result.get("choices")[0].get("message")
        logging.info(f"response message: {resp}")

        if number_of_messages_to_keep:
            # cache the response
            redis_conn.rpush(user_id, json.dumps(Message(role=resp.get("role"), content=resp.get("content")).__dict__))

            # Keep only the last {number_of_messages_to_keep} messages
            redis_conn.ltrim(user_id, 0, number_of_messages_to_keep - 1)

        # Sending results messages
        return Response(resp.get("content"))
    except KeyError as e:
        logging.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=e)
