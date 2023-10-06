import logging
import re

from fastapi import APIRouter
from slack_sdk import WebClient
from starlette.background import BackgroundTasks
from starlette.responses import Response

from app.config.constants import openai_token, slack_token, number_of_messages_to_keep, model
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
    client = WebClient(token=slack_token)

    # Parsing the request message.
    content = re.sub(r"<@(.*?)>", "", event.get("text")).lstrip()
    request_message = Message(role="user", content=content)
    logging.info(f"[{thread_ts}][{api_app_id}:{channel}:{user}] request_message: {request_message}")

    # Get past chat history and fit it into the ChatGPT format.
    conversations_replies = client.conversations_replies(channel=channel, ts=thread_ts)
    chat_history = conversations_replies.data.get("messages")[-1 * number_of_messages_to_keep:]
    messages = []
    for history in chat_history:
        if "app_id" in history:
            messages.append(Message(role="assistant", content=history.get("text")).__dict__)
        else:
            messages.append(Message(role="user", content=history.get("text")).__dict__)
    messages.append(request_message.__dict__)

    # Send messages to the ChatGPT server and respond to Slack
    response_message = get_chatgpt(
        api_key=openai_token,
        messages=messages,
        model=model if model else Model.GPT_3_5_TURBO.value,
        max_tokens=2048,
        temperature=0.7,
        top_p=1,
        presence_penalty=0.5,
        frequency_penalty=0.5,
    )

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

    logging.info(f"[{thread_ts}][{api_app_id}:{channel}:{user}] response_message: {message}")


@router.post("")
async def slack(message: dict, background_tasks: BackgroundTasks):
    if message.get("challenge"):
        return message.get("challenge")

    # Because Slack is constrained to give a response in 3 seconds, ChatGPT processing is handled by background_tasks.
    background_tasks.add_task(call_chatgpt, message)
    return Response("ok")
