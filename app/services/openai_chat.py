import logging
from enum import Enum

import openai
from fastapi import Query
from openai.error import AuthenticationError, InvalidRequestError, RateLimitError, Timeout
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
    retry_if_exception_type,
)  # for exponential backoff

from app.config.constants import system_content
from app.config.messages import (
    model_description,
    max_tokens_description,
    temperature_description,
    top_p_description,
    presence_penalty_description,
    frequency_penalty_description,
)


class Model(Enum):
    GPT4_TURBO = "gpt-4-turbo"
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
    messages: list,
    model: str = Query(Model.GPT_3_5_TURBO.value, description=model_description),
    max_tokens: int = Query(2048, description=max_tokens_description),
    temperature: float = Query(0.7, description=temperature_description),
    top_p: float = Query(1, description=top_p_description),
    presence_penalty: float = Query(0.5, description=presence_penalty_description),
    frequency_penalty: float = Query(0.5, description=frequency_penalty_description),
):
    openai.api_key = api_key

    if system_content:
        messages.insert(0, {"role": "system", "content": system_content})

    # https://platform.openai.com/docs/api-reference/completions/create
    try:
        response = await completions_with_backoff(
            model=model,
            stream=True,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            presence_penalty=presence_penalty,
            frequency_penalty=frequency_penalty,
            messages=messages,
            request_timeout=300,
        )
    except AuthenticationError as e:
        logging.error(e)
        raise Exception("The token is invalid.")
    except InvalidRequestError as e:
        logging.error(e)
        if "This model's maximum context length is 4097 tokens" in str(e):
            raise Exception("너무 긴 답변을 유도하셨습니다. 이미지를 첨부하셨다면 글자가 너무 많지 않은지 확인해주세요.")
        else:
            raise Exception("오류가 발생했습니다 :sob: 다시 시도해 주세요.")
    except Timeout as e:
        logging.error(e)
        raise Exception("OpenAI 서버가 응답이 없습니다. 다시 시도해 주세요.")
    except Exception as e:
        logging.exception(e)
        raise Exception("오류가 발생했습니다 :sob: 다시 시도해 주세요.")

    try:
        collected_messages = []
        async for chunk in response:
            chunk_message = chunk["choices"][0]["delta"].get("content")
            collected_messages.append(chunk_message)
            yield chunk_message if chunk_message else " "
    except KeyError as e:
        logging.exception(e)
        raise Exception("오류가 발생했습니다 :sob: 다시 시도해 주세요.")
