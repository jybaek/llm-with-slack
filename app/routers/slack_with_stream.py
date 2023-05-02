import asyncio
import logging
import re

from fastapi import APIRouter
from slack_sdk import WebClient
from starlette.background import BackgroundTasks
from starlette.responses import Response

from app.config.constants import openai_token, slack_token, number_of_messages_to_keep, model
from app.google.vision import text_detection, localize_objects
from app.services.openai_chat import get_chatgpt, Message, Model
from app.services.openai_images import get_images, ImageSize, ResponseFormat

router = APIRouter()


async def write_notification(slack_message: dict):
    # Set the data to send
    event = slack_message.get("event")
    channel = event.get("channel")
    thread_ts = event.get("thread_ts") if event.get("thread_ts") else event.get("ts")
    attachments = []

    # Image processing
    system_message = ""
    if files := event.get("files"):
        texts_in_image = text_detection(files)
        object_in_image = localize_objects(files)
        system_message = "\n".join(
            [
                f"{index} 번째 사진에는 다음과 같은 글자와 객체가 있어. {text}, {object_}."
                for index, (text, object_) in enumerate(zip(texts_in_image, object_in_image), 1)
            ]
        )
        system_message += "이제 이 사진에 대해서 질문 할 거야. "

    content = re.sub(r"<@(.*?)>", "", event.get("text")).lstrip()

    # If it starts with !, it will create the image via DALL-E
    if content.startswith("!"):
        logging.info(f"request_message: {content}")

        # Send messages to the ChatGPT server and respond to Slack
        images = asyncio.run(
            get_images(
                api_key=openai_token,
                message=content,
                n=1,
                size=ImageSize.SIZE_512,
                response_format=ResponseFormat.URL,
            )
        )
        attachments = [{"title": f"{index}", "image_url": image.get("url")} for index, image in enumerate(images)]
        response_message = ""
    else:
        request_message = Message(role="user", content=system_message + content)
        logging.info(f"request_message: {request_message}")

        # Send messages to the ChatGPT server and respond to Slack
        response_message = get_chatgpt(
                api_key=openai_token,
                message=request_message,
                model=model if model else Model.GPT_3_5_TURBO.value,
                max_tokens=2048,
                temperature=1,
                top_p=1,
                presence_penalty=0.5,
                frequency_penalty=0.5,
                context_unit=thread_ts,
                number_of_messages_to_keep=number_of_messages_to_keep,
            )

    client = WebClient(token=slack_token)
    first_message = True
    message = ""
    ts = ""
    try:
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

    logging.info(f"response_message: {message}")


@router.post("")
async def slack(message: dict, background_tasks: BackgroundTasks):
    if message.get("challenge"):
        return message.get("challenge")

    # Because Slack is constrained to give a response in 3 seconds, ChatGPT processing is handled by background_tasks.
    background_tasks.add_task(write_notification, message)

    logging.info("response ok")
    return Response("ok")
