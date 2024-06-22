import re
import tempfile

from anthropic import AnthropicVertex
from app.config.constants import google_cloud_project_name, number_of_messages_to_keep, claude_model

LOCATION = "europe-west1"  # or "us-east5"

client = AnthropicVertex(region=LOCATION, project_id=google_cloud_project_name)


async def build_claude_message(slack_client, channel: str, thread_ts: str):
    # Get past chat history and fit it into the Gemini format.
    conversations_replies = slack_client.conversations_replies(channel=channel, ts=thread_ts)
    chat_history = conversations_replies.data.get("messages")[-1 * number_of_messages_to_keep :]
    messages = []
    content = ""
    with tempfile.TemporaryDirectory() as dir_path:
        for index, history in enumerate(chat_history, start=1):
            role = "model" if "app_id" in history else "user"
            # 사용자와 모델이 메시지를 번갈아가면서 주고받지 않으면 오류가 발생하기 때문에 아래와 같은 처리를 함
            if role == "user":
                content = f"{content}. {history.get('text')}" if content else history.get("text")
                if index == len(chat_history):
                    content = re.sub(r"<@(.*?)>", "", content).lstrip()
                    messages.append({"role": "user", "content": content})
            else:
                messages.append({"role": "user", "content": content})
                messages.append({"role": "assistant", "content": history.get("text")})
                content = ""

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
