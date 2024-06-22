import logging
import re
import tempfile

from anthropic import AnthropicVertex
from app.config.constants import google_cloud_project_name, number_of_messages_to_keep, claude_model, MAX_FILE_BYTES
from app.utils.file import download_file, encode_image

LOCATION = "europe-west1"  # or "us-east5"

client = AnthropicVertex(region=LOCATION, project_id=google_cloud_project_name)


async def build_claude_message(slack_client, channel: str, thread_ts: str):
    # Get past chat history and fit it into the Gemini format.
    conversations_replies = slack_client.conversations_replies(channel=channel, ts=thread_ts)
    chat_history = conversations_replies.data.get("messages")[-1 * number_of_messages_to_keep :]
    messages = []
    images = []
    content = ""
    with tempfile.TemporaryDirectory() as dir_path:
        for index, history in enumerate(chat_history, start=1):
            role = "model" if "app_id" in history else "user"
            # 사용자와 모델이 메시지를 번갈아가면서 주고받지 않으면 오류가 발생하기 때문에 아래와 같은 처리를 함
            if role == "user":
                content = f"{content}. {history.get('text')}" if content else history.get("text")
                if files := history.get("files", []):
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
                if index == len(chat_history):
                    if list(filter(lambda x: x["size"] > MAX_FILE_BYTES, files)):
                        raise Exception(f"서버 비용 문제로 {MAX_FILE_BYTES/1000/1000}MB 이상되는 이미지는 처리할 수 없습니다")
                    content = re.sub(r"<@(.*?)>", "", content).lstrip()
                    if images:
                        images.append({"type": "text", "text": content})
                        messages.append({"role": "user", "content": images})
                    else:
                        messages.append({"role": "user", "content": content})
            else:
                if images:
                    images.append({"type": "text", "text": content})
                    messages.append({"role": "user", "content": images})
                else:
                    messages.append({"role": "user", "content": content})
                messages.append({"role": "assistant", "content": history.get("text")})
                content = ""
                images = []

    return messages


async def get_claude(messages):
    with client.messages.stream(
        max_tokens=1024,
        messages=messages,
        model=claude_model,
    ) as stream:
        for text in stream.text_stream:
            yield text if text else " "
    yield " "
