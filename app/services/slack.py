import logging
import re
import tempfile
from uuid import uuid4

from openai import BadRequestError
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from app.config.constants import (
    slack_token,
    gpt_model,
    LLMModel,
    openai_token,
    max_token,
)
from app.services.anthropic_claude import build_claude_message, get_claude
from app.services.google_gemini import build_gemini_message, get_gemini
from app.services.openai_chat import get_chatgpt, Model, build_chatgpt_message
from app.services.openai_images import generate_image
from app.utils.file import download_file
from app.utils.message import async_generator


async def message_process(slack_message: dict, llm_model: LLMModel):
    slack_client = WebClient(token=slack_token)
    event = slack_message.get("event")
    channel = event.get("channel")
    thread_ts = event.get("thread_ts") if event.get("thread_ts") else event.get("ts")
    user = event.get("user")
    api_app_id = slack_message.get("api_app_id")

    try:
        if llm_model == LLMModel.GPT:
            content = re.sub(r"<@(.*?)>", "", event.get("text")).lstrip()
            if content.startswith("!"):
                image_url_link = await generate_image(
                    api_key=openai_token, prompt=content, size="1024x1024", quality="standard"
                )
                with tempfile.TemporaryDirectory() as dir_path:
                    filename = f"{dir_path}/{uuid4()}"
                    if download_file(image_url_link, filename):
                        return slack_client.files_upload_v2(
                            channel=channel,
                            thread_ts=thread_ts,
                            title="DALL-E",
                            file=filename,
                        )
                    else:
                        raise Exception(f"Error - download_file failed")
            else:
                # Set the data to send
                messages = await build_chatgpt_message(slack_client, channel, thread_ts)

                # Send messages to the ChatGPT server and respond to Slack
                response_message = get_chatgpt(
                    messages=messages,
                    gpt_model=gpt_model if gpt_model else Model.GPT_3_5_TURBO.value,
                    max_tokens=max_token,
                    temperature=0.7,
                    top_p=1,
                    presence_penalty=0.5,
                    frequency_penalty=0.5,
                )
        elif llm_model == LLMModel.GEMINI:
            chat, content = await build_gemini_message(slack_client, channel, thread_ts)
            response_message = get_gemini(chat, content)
        elif llm_model == LLMModel.CLAUDE:
            messages = await build_claude_message(slack_client, channel, thread_ts)
            response_message = get_claude(messages)
        else:
            raise Exception(f"Error - Unknown model: {llm_model}")
    except BadRequestError as e:
        if e.code == "content_policy_violation":
            response_message = async_generator(
                f"{e.body.get('message')}: 이미지 생성 요청에 부적합한 단어가 사용됐습니다. 표현을 변경해서 다시 시도해 주세요."
            )
        else:
            response_message = async_generator(e.__str__())
    except Exception as e:
        response_message = async_generator(e.__str__())

    logging.info(f"[{thread_ts}][{api_app_id}:{channel}:{user}] request_message: {event.get('text')}")
    message = ts = ""
    try:
        async for chunk in response_message:
            message += chunk
            post_message = False
            api_error = False
            if not ts:
                post_message = True
            else:
                # Logic to avoid Slack rate limits.
                if len(message) % 10 == 0:
                    try:
                        slack_client.chat_update(channel=channel, text=message, ts=ts, as_user=True)
                    except SlackApiError as e:
                        if e.response["error"] == "msg_too_long":
                            post_message = True
                            api_error = True
                        else:
                            raise
            if post_message:
                if api_error:
                    message = chunk
                result = slack_client.chat_postMessage(
                    channel=channel, text=message, thread_ts=thread_ts, attachments=[]
                )
                ts = result["ts"]

        # Handle the last message from the generator
        slack_client.chat_update(channel=channel, text=message, ts=ts, as_user=True)
    except Exception as e:
        slack_client.chat_postMessage(channel=channel, text=str(e), thread_ts=thread_ts, attachments=[])

    logging.info(f"[{thread_ts}][{api_app_id}:{channel}:{user}] response_message: {message}")
