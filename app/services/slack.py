import logging
import tempfile

from slack_sdk import WebClient

from app.config.constants import slack_token, number_of_messages_to_keep, model, openai_token
from app.services.openai_chat import get_chatgpt, Model
from app.utils.file import download_file, encode_image

client = WebClient(token=slack_token)


async def build_chatgpt_message(channel: str, thread_ts: str, user: str, api_app_id: str):
    # Get past chat history and fit it into the ChatGPT format.
    conversations_replies = client.conversations_replies(channel=channel, ts=thread_ts)
    chat_history = conversations_replies.data.get("messages")[-1 * number_of_messages_to_keep :]
    messages = []
    with tempfile.TemporaryDirectory() as dir_path:
        for history in chat_history:
            role = "assistant" if "app_id" in history else "user"
            content = []
            if model == "gpt-4-turbo" and (files := history.get("files")):
                for file in files:
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
            content.append({"type": "text", "text": history.get("text")})
            messages.append({"role": role, "content": content})
    logging.info(f"[{thread_ts}][{api_app_id}:{channel}:{user}] request_message: {messages[-1].get('content')}")
    return messages


async def message_process(slack_message: dict):
    event = slack_message.get("event")
    channel = event.get("channel")
    thread_ts = event.get("thread_ts") if event.get("thread_ts") else event.get("ts")
    user = event.get("user")
    api_app_id = slack_message.get("api_app_id")

    # Set the data to send
    messages = await build_chatgpt_message(channel, thread_ts, user, api_app_id)

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

    message = ts = ""
    try:
        async for chunk in response_message:
            message += chunk
            if not ts:
                result = client.chat_postMessage(channel=channel, text=message, thread_ts=thread_ts, attachments=[])
                ts = result["ts"]
            else:
                # Logic to avoid Slack rate limits.
                if len(message) % 10 == 0 or (len(chunk) == 1 and chunk == " "):
                    client.chat_update(channel=channel, text=message, ts=ts, as_user=True)
    except Exception as e:
        client.chat_postMessage(channel=channel, text=str(e), thread_ts=thread_ts, attachments=[])

    logging.info(f"[{thread_ts}][{api_app_id}:{channel}:{user}] response_message: {message}")
