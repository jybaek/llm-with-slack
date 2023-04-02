import logging
from enum import Enum

import openai
from fastapi import Query
from openai.error import AuthenticationError, InvalidRequestError, RateLimitError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
    retry_if_exception_type,
)  # for exponential backoff

from app.config.messages import (
    model_description,
    max_tokens_description,
    temperature_description,
    top_p_description,
    presence_penalty_description,
    frequency_penalty_description,
)


class Model(Enum):
    TEXT_DAVINCI_003 = "text-davinci-003"


@retry(
    wait=wait_random_exponential(min=2, max=5),
    stop=stop_after_attempt(5),
    retry=retry_if_exception_type(RateLimitError),
)
async def completions_with_backoff(**kwargs):
    return await openai.Completion.acreate(**kwargs)


async def get_completions(
    api_key: str,
    message: str,
    model: Model = Query(Model.TEXT_DAVINCI_003, description=model_description),
    max_tokens: int = Query(2048, description=max_tokens_description),
    temperature: float = Query(1, description=temperature_description),
    top_p: float = Query(1, description=top_p_description),
    presence_penalty: float = Query(0.5, description=presence_penalty_description),
    frequency_penalty: float = Query(0.5, description=frequency_penalty_description),
):
    openai.api_key = api_key

    # https://platform.openai.com/docs/api-reference/completions
    try:
        result = await completions_with_backoff(
            model=model.value,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            presence_penalty=presence_penalty,
            frequency_penalty=frequency_penalty,
            prompt=message,
            request_timeout=60,
        )
    except AuthenticationError as e:
        logging.error(e)
        return "The token is invalid."
    except InvalidRequestError as e:
        logging.error(e)
        if "This model's maximum context length is 4097 tokens" in str(e):
            return "너무 긴 답변을 유도하셨습니다."
        else:
            return "오류가 발생했습니다 :sob: 다시 시도해 주세요."
    except Exception as e:
        logging.exception(e)
        return "오류가 발생했습니다 :sob: 다시 시도해 주세요."

    try:
        return result.get("choices")[0].get("text")
    except KeyError as e:
        logging.exception(e)
        return "오류가 발생했습니다 :sob: 다시 시도해 주세요."
