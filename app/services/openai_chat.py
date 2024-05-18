import logging
import re
import tempfile
from enum import Enum

from openai import AsyncOpenAI
from fastapi import Query
from openai._exceptions import AuthenticationError, BadRequestError, RateLimitError, APITimeoutError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
    retry_if_exception_type,
)  # for exponential backoff

from app.config.constants import system_content, number_of_messages_to_keep, gpt_model, MAX_FILE_BYTES, openai_token
from app.config.messages import (
    model_description,
    max_tokens_description,
    temperature_description,
    top_p_description,
    presence_penalty_description,
    frequency_penalty_description,
)
from app.utils.file import download_file, encode_image


class Model(Enum):
    GPT4_TURBO = "gpt-4-turbo"
    GPT_3_5_TURBO = "gpt-3.5-turbo"


client = AsyncOpenAI(api_key=openai_token)


@retry(
    wait=wait_random_exponential(min=2, max=5),
    stop=stop_after_attempt(5),
    retry=retry_if_exception_type(RateLimitError),
)
async def completions_with_backoff(**kwargs):
    return await client.chat.completions.create(**kwargs)


async def get_chatgpt(
    messages: list,
    gpt_model: str = Query(Model.GPT_3_5_TURBO.value, description=model_description),
    max_tokens: int = Query(2048, description=max_tokens_description),
    temperature: float = Query(0.7, description=temperature_description),
    top_p: float = Query(1, description=top_p_description),
    presence_penalty: float = Query(0.5, description=presence_penalty_description),
    frequency_penalty: float = Query(0.5, description=frequency_penalty_description),
):

    if system_content:
        messages.insert(0, {"role": "system", "content": system_content})

    # https://platform.openai.com/docs/api-reference/completions/create
    try:
        response = await completions_with_backoff(
            model=gpt_model,
            stream=True,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            presence_penalty=presence_penalty,
            frequency_penalty=frequency_penalty,
            messages=messages,
        )
    except AuthenticationError as e:
        logging.error(e)
        raise Exception("The token is invalid.")
    except BadRequestError as e:
        logging.error(e)
        if "This model's maximum context length is 4097 tokens" in str(e):
            raise Exception("너무 긴 답변을 유도하셨습니다. 이미지를 첨부하셨다면 글자가 너무 많지 않은지 확인해주세요.")
        else:
            raise Exception("오류가 발생했습니다 :sob: 다시 시도해 주세요.")
    except APITimeoutError as e:
        logging.error(e)
        raise Exception("OpenAI 서버가 응답이 없습니다. 다시 시도해 주세요.")
    except Exception as e:
        logging.exception(e)
        raise Exception("오류가 발생했습니다 :sob: 다시 시도해 주세요.")

    try:
        collected_messages = []
        async for chunk in response:
            chunk_message = chunk.choices[0].delta.content
            collected_messages.append(chunk_message)
            yield chunk_message if chunk_message else " "
    except KeyError as e:
        logging.exception(e)
        raise Exception("오류가 발생했습니다 :sob: 다시 시도해 주세요.")


async def build_chatgpt_message(slack_client, channel: str, thread_ts: str):
    # Get past chat history and fit it into the ChatGPT format.
    conversations_replies = slack_client.conversations_replies(channel=channel, ts=thread_ts)
    chat_history = conversations_replies.data.get("messages")[-1 * number_of_messages_to_keep :]
    messages = []
    with tempfile.TemporaryDirectory() as dir_path:
        for index, history in enumerate(chat_history, start=1):
            role = "assistant" if "app_id" in history else "user"
            content = []
            if gpt_model == "gpt-4-turbo" and (files := history.get("files", [])):
                for file in files:
                    if file.get("size") > MAX_FILE_BYTES:
                        continue
                    url = file.get("url_private")
                    filename = f"{dir_path}/{file.get('name')}"
                    if download_file(url, filename):
                        content.append(
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:{file.get('mimetype')};base64,{encode_image(filename)}"},
                            }
                        )
                    else:
                        logging.warning("Failed - Download error")
                if index == len(chat_history):
                    if list(filter(lambda x: x["size"] > MAX_FILE_BYTES, files)):
                        raise Exception(f"서버 비용 문제로 {MAX_FILE_BYTES/1000/1000}MB 이상되는 이미지는 처리할 수 없습니다")
            content.append({"type": "text", "text": re.sub(r"<@(.*?)>", "", history.get("text"))})
            messages.append({"role": role, "content": content})
    return messages
