import json
import logging
from enum import Enum

import openai
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


class Message(BaseModel):
    role: str = "user"
    content: str


class Model(Enum):
    GPT_3_5_TURBO = "gpt-3.5-turbo"


@retry(
    wait=wait_random_exponential(min=2, max=5),
    stop=stop_after_attempt(5),
    retry=retry_if_exception_type(RateLimitError),
)
async def completions_with_backoff(**kwargs):
    return await openai.ChatCompletion.acreate(**kwargs)


async def get_chatgpt(
    api_key: str,
    message: Message,
    model: Model = Model.GPT_3_5_TURBO,
    max_tokens: int = 2048,
    presence_penalty: float = 0.5,
    frequency_penalty: float = 0.5,
    context_unit: str = "u_1234",
    number_of_messages_to_keep: int = 6,
):
    openai.api_key = api_key
    messages = []

    # Fetch cached messages.
    if number_of_messages_to_keep:
        redis_conn = RedisClient().get_conn()
        messages = [json.loads(message) for message in redis_conn.lrange(context_unit, 0, -1)]

    # https://platform.openai.com/docs/api-reference/completions/create
    try:
        result = await completions_with_backoff(
            model=model.value,
            max_tokens=max_tokens,
            presence_penalty=presence_penalty,
            frequency_penalty=frequency_penalty,
            messages=messages + [message.__dict__],
            request_timeout=30,
        )
    except AuthenticationError as e:
        logging.error(e)
        return "The token is invalid."
    except InvalidRequestError as e:
        logging.error(e)
        if "This model's maximum context length is 4097 tokens" in str(e):
            redis_conn.delete(context_unit)
            return "너무 긴 답변을 유도하셨습니다. 이미지를 첨부하셨다면 글자가 너무 많지 않은지 확인해주세요."
        else:
            return "오류가 발생했습니다 :sob: 다시 시도해 주세요."
    except Exception as e:
        logging.exception(e)
        if number_of_messages_to_keep:
            redis_conn.lpop(context_unit)
            redis_conn.lpop(context_unit)
        return "오류가 발생했습니다 :sob: 다시 시도해 주세요."

    try:
        resp = result.get("choices")[0].get("message")

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
        return resp.get("content")
    except KeyError as e:
        logging.exception(e)
        return "오류가 발생했습니다 :sob: 다시 시도해 주세요."
