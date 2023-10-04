import logging
import re

from fastapi import APIRouter
from slack_sdk import WebClient
from starlette.background import BackgroundTasks
from starlette.responses import Response

from app.config.constants import openai_token, slack_token, number_of_messages_to_keep, model, slack_token2
from app.google.vision import text_detection, localize_objects
from app.services.google_palm import get_palm_chat
from app.services.openai_chat import get_chatgpt, Message, Model

router = APIRouter()


async def call_chatgpt(slack_message: dict):
    # Set the data to send
    event = slack_message.get("event")
    channel = event.get("channel")
    user = event.get("user")
    api_app_id = slack_message.get("api_app_id")
    thread_ts = event.get("thread_ts") if event.get("thread_ts") else event.get("ts")
    attachments = []
    image_summary = ""

    # Image processing
    if files := event.get("files"):
        texts_in_image = text_detection(files)
        object_in_image = localize_objects(files)
        image_summary = "\n".join(
            [
                f"{index} 번째 사진에는 다음과 같은 글자와 객체가 있어. {text}, {object_}."
                for index, (text, object_) in enumerate(zip(texts_in_image, object_in_image), 1)
            ]
        )
        image_summary += "이제 이 사진에 대해서 질문 할 거야. "

    content = re.sub(r"<@(.*?)>", "", event.get("text")).lstrip()

    request_message = Message(role="user", content=image_summary + content)
    logging.info(f"[{thread_ts}][{api_app_id}:{channel}:{user}] request_message: {request_message}")

    # Send messages to the ChatGPT server and respond to Slack
    response_message = get_chatgpt(
        api_key=openai_token,
        message=request_message,
        model=model if model else Model.GPT_3_5_TURBO.value,
        max_tokens=2048,
        temperature=0.7,
        top_p=1,
        presence_penalty=0.5,
        frequency_penalty=0.5,
        context_unit=thread_ts,
        number_of_messages_to_keep=number_of_messages_to_keep,
    )

    first_message = True
    message = ""
    ts = ""
    try:
        client = WebClient(token=slack_token)
        async for chunk in response_message:
            message += chunk
            if first_message:
                result = client.chat_postMessage(
                    channel=channel,
                    text=message,
                    thread_ts=thread_ts,
                    attachments=attachments,
                )
                first_message = False
                ts = result["ts"]
            else:
                if len(message) % 10 == 0:
                    client.chat_update(
                        channel=channel,
                        text=message,
                        ts=ts,
                        as_user=True,
                    )
        client.chat_update(
            channel=channel,
            text=message,
            ts=ts,
            as_user=True,
        )
    except Exception as e:
        client.chat_postMessage(
            channel=channel,
            text=str(e),
            thread_ts=thread_ts,
            attachments=attachments,
        )

    logging.info(f"[{thread_ts}][{api_app_id}:{channel}:{user}] response_message: {message}")


async def call_palm(slack_message: dict):
    # Set the data to send
    event = slack_message.get("event")
    channel = event.get("channel")
    user = event.get("user")
    api_app_id = slack_message.get("api_app_id")
    thread_ts = event.get("thread_ts") if event.get("thread_ts") else event.get("ts")

    content = re.sub(r"<@(.*?)>", "", event.get("text")).lstrip()
    logging.info(f"[{thread_ts}][{api_app_id}:{channel}:{user}] request_message: {content}")

    response_message = await get_palm_chat(
        message=content,
        context_unit=thread_ts
    )
    client = WebClient(token=slack_token2)
    client.chat_postMessage(
        channel=channel,
        text=response_message,
        thread_ts=event.get("ts") if event.get("ts") else event.get("thread_ts"),
    )

    logging.info(f"[{thread_ts}][{api_app_id}:{channel}:{user}] response_message: {response_message}")


@router.post("")
async def slack(message: dict, background_tasks: BackgroundTasks):
    if message.get("challenge"):
        return message.get("challenge")

    if message.get("api_app_id") == "A03LFTM5C15":  # caley-bot
        # Because Slack is constrained to give a response in 3 seconds, ChatGPT processing is handled by background_tasks.
        background_tasks.add_task(call_chatgpt, message)
    else:
        background_tasks.add_task(call_palm, message)


    logging.info("response ok")
    return Response("ok")
