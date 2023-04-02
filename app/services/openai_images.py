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


class Model(Enum):
    TEXT_DAVINCI_003 = "text-davinci-003"


class ImageSize(Enum):
    SIZE_256 = "256x256"
    SIZE_512 = "512x512"
    SIZE_1024 = "1024x1024"


class ResponseFormat(Enum):
    URL = "url"
    B64_JSON = "b64_json"


@retry(
    wait=wait_random_exponential(min=2, max=5),
    stop=stop_after_attempt(5),
    retry=retry_if_exception_type(RateLimitError),
)
async def completions_with_backoff(**kwargs):
    return await openai.Image.acreate(**kwargs)


async def get_images(
    api_key: str,
    message: str,
    n: int = Query(1, description="The number of images to generate. Must be between 1 and 10."),
    size: ImageSize = Query(ImageSize.SIZE_1024, description="The size of the generated images"),
    response_format: ResponseFormat = Query(
        ResponseFormat.URL, description="The format in which the generated images are returned"
    ),
):
    openai.api_key = api_key

    # https://platform.openai.com/docs/api-reference/images/create
    try:
        result = await completions_with_backoff(
            prompt=message,
            n=n,
            size=size.value,
            response_format=response_format.value,
        )
    except AuthenticationError as e:
        logging.error(e)
        return "The token is invalid."
    except InvalidRequestError as e:
        return "유효하지 않은 요청입니다. 다시 시도해 주세요."
    except Exception as e:
        logging.exception(e)
        return "오류가 발생했습니다 :sob: 다시 시도해 주세요."

    try:
        return result.get("data")
    except KeyError as e:
        logging.exception(e)
        return "오류가 발생했습니다 :sob: 다시 시도해 주세요."
