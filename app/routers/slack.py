import asyncio
import logging

from fastapi import APIRouter
from slack_sdk import WebClient
from starlette.background import BackgroundTasks
from starlette.responses import Response

from app.config.constants import openai_token, slack_token, number_of_messages_to_keep
from app.google.vision import text_detection, localize_objects
from app.services.openai_service import get_chatgpt, Message, Model

router = APIRouter()


def write_notification(slack_message: dict):
    # Set the data to send
    event = slack_message.get("event")
    channel = event.get("channel")
    thread_ts = event.get("thread_ts") if event.get("thread_ts") else event.get("ts")

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

    content = "".join(event.get("text").split("> ")[1:])
    request_message = Message(role="user", content=system_message + content)

    logging.info(f"request_message: {request_message}")

    # Send messages to the ChatGPT server and respond to Slack
    response_message = asyncio.run(
        get_chatgpt(
            api_key=openai_token,
            message=request_message,
            model=Model.GPT_3_5_TURBO,
            context_unit=thread_ts,
            number_of_messages_to_keep=number_of_messages_to_keep,
        )
    )
    logging.info(f"response_message: {response_message}")
    client = WebClient(token=slack_token)
    client.chat_postMessage(
        channel=channel, text=response_message, thread_ts=event.get("ts") if event.get("ts") else event.get("thread_ts")
    )


@router.post("/slack")
async def slack(message: dict, background_tasks: BackgroundTasks):
    if message.get("challenge"):
        return message.get("challenge")

    # Because Slack is constrained to give a response in 3 seconds, ChatGPT processing is handled by background_tasks.
    background_tasks.add_task(write_notification, message)

    logging.info("response ok")
    return Response("ok")
