import json
import logging
from enum import Enum

import openai
from fastapi import APIRouter, Security
from fastapi.security import APIKeyHeader
from openai.error import AuthenticationError, InvalidRequestError, RateLimitError
from pydantic import BaseModel
from starlette.responses import Response
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
    retry_if_exception_type,
)  # for exponential backoff

from app.config.constants import MESSAGE_EXPIRE_TIME
from app.models.redis import RedisClient

API_KEY_NAME = "X-API-KEY"
router = APIRouter()

logging.getLogger("backoff").setLevel(logging.ERROR)


class Message(BaseModel):
    role: str = "user"
    content: str


class Model(Enum):
    GPT_3_5_TURBO = "gpt-3.5-turbo"


@router.get("/models")
async def models(api_key: str = Security(APIKeyHeader(name=API_KEY_NAME, auto_error=True))):
    openai.api_key = api_key

    return await openai.Model.alist()


@retry(
    wait=wait_random_exponential(min=2, max=5),
    stop=stop_after_attempt(5),
    retry=retry_if_exception_type(RateLimitError),
)
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
    context_unit: str = "u_1234",
    number_of_messages_to_keep: int = 5,
):
    logging.info(f"request message: {message.__dict__}")
    openai.api_key = api_key
    messages = []

    # Fetch cached messages.
    if number_of_messages_to_keep:
        redis_conn = RedisClient().get_conn()
        messages = [json.loads(message) for message in redis_conn.lrange(context_unit, 0, -1)]

    # https://platform.openai.com/docs/api-reference/completions/create
    try:
        result = completions_with_backoff(
            model=model.value,
            max_tokens=max_tokens,
            presence_penalty=presence_penalty,
            frequency_penalty=frequency_penalty,
            messages=messages + [message.__dict__],
            request_timeout=30,
        )
    except AuthenticationError as e:
        logging.error(e)
        return Response("The token is invalid.")
    except InvalidRequestError as e:
        logging.error(e)
        if "This model's maximum context length is 4097 tokens" in str(e):
            redis_conn.delete(context_unit)
            return Response("너무 긴 답변을 유도하셨습니다. 이미지를 첨부하셨다면 글자가 너무 많지 않은지 확인해주세요.")
        else:
            return Response("오류가 발생했습니다 :sob: 다시 시도해 주세요.")
    except Exception as e:
        logging.exception(e)
        if number_of_messages_to_keep:
            redis_conn.lpop(context_unit)
            redis_conn.lpop(context_unit)
        return Response("오류가 발생했습니다 :sob: 다시 시도해 주세요.")

    try:
        resp = result.get("choices")[0].get("message")
        logging.info(f"response message: {resp}")

        if number_of_messages_to_keep:
            # cache the response
            redis_conn.rpush(context_unit, json.dumps(message.__dict__))
            redis_conn.rpush(
                context_unit, json.dumps(Message(role=resp.get("role"), content=resp.get("content")).__dict__)
            )

            # Keep only the last {number_of_messages_to_keep} messages
            redis_conn.ltrim(context_unit, number_of_messages_to_keep * -1, -1)
            redis_conn.expire(context_unit, MESSAGE_EXPIRE_TIME)

        # Sending results messages
        return Response(resp.get("content"))
    except KeyError as e:
        logging.exception(e)
        return Response("오류가 발생했습니다 :sob: 다시 시도해 주세요.")
