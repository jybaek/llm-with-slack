import logging
import re
import tempfile

from anthropic import AsyncAnthropicVertex
from app.config.constants import (
    google_cloud_project_name,
    number_of_messages_to_keep,
    claude_model,
    MAX_FILE_BYTES,
    max_token,
)
from app.utils.file import download_file, encode_image

LOCATION = "europe-west1"  # or "us-east5"

client = AsyncAnthropicVertex(region=LOCATION, project_id=google_cloud_project_name)


async def build_claude_message(slack_client, channel: str, thread_ts: str):
    # Get past chat history and fit it into the Gemini format.
    conversations_replies = slack_client.conversations_replies(channel=channel, ts=thread_ts)
    chat_history = conversations_replies.data.get("messages")[-1 * number_of_messages_to_keep :]
    messages = []
    images = []
    corpora = []
    content = ""
    with tempfile.TemporaryDirectory() as dir_path:
        comment = []
        corpora.append(comment)
        for index, history in enumerate(chat_history, start=1):
            role = "assistant" if "app_id" in history else "user"
            if not comment or comment[-1]["role"] == role:
                comment.append({"role": role, "history": history})
            else:
                comment = []
                corpora.append(comment)
                history["text"] = re.sub(r"<@(.*?)>", "", history.get("text")).lstrip()
                comment.append({"role": role, "history": history})

        for corpus in corpora:
            for message in corpus:
                content = f"{content}. {message['history'].get('text')}" if content else message['history'].get("text")
                if files := message['history'].get("files", []):
                    for file in files:
                        if file.get("size") > MAX_FILE_BYTES:
                            continue
                        url = file.get("url_private")
                        filename = f"{dir_path}/{file.get('name')}"
                        if download_file(url, filename):
                            images.append(
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": file.get("mimetype"),
                                        "data": encode_image(filename),
                                    },
                                }
                            )
                        else:
                            logging.warning("Failed - Download error")

            role = corpus[0].get("role")
            if images:
                images.append({"type": "text", "text": content})
                messages.append({"role": role, "content": images})
            else:
                messages.append({"role": role, "content": content})
            content = ""
            images = []

    return messages


async def get_claude(messages):
    async with client.messages.stream(
        max_tokens=max_token,
        messages=messages,
        model=claude_model,
    ) as stream:
        async for text in stream.text_stream:
            yield text
