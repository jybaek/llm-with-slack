import logging
import tempfile

import vertexai

from app.config.constants import number_of_messages_to_keep
from vertexai.generative_models import GenerativeModel, Content, Part, Image
import vertexai.preview.generative_models as generative_models

from app.utils.file import download_file

vertexai.init(project="gde-cloud-project", location="us-central1")
model = GenerativeModel(
    "gemini-1.5-pro-preview-0409",
)

generation_config = {
    "max_output_tokens": 8192,
    "temperature": 1,
    "top_p": 0.95,
}

safety_settings = {
    generative_models.HarmCategory.HARM_CATEGORY_HATE_SPEECH: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    generative_models.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    generative_models.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    generative_models.HarmCategory.HARM_CATEGORY_HARASSMENT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
}


async def build_gemini_message(slack_client, channel: str, thread_ts: str, user: str, api_app_id: str):
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
                content = f"{content}. {history.get('text')}"
                if files := history.get("files"):
                    for file in files:
                        url = file.get("url_private")
                        filename = f"{dir_path}/{file.get('name')}"
                        if download_file(url, filename):
                            images.append(filename)
                        else:
                            logging.warning("Failed - Download error")
                if index == len(chat_history):
                    parts = [Part.from_text(content)]
                    if images:
                        parts.extend([Part.from_image(Image.load_from_file(image)) for image in images])
                    messages.append(Content(role="user", parts=parts))
            else:
                parts = [Part.from_text(content)]
                if images:
                    parts.extend([Part.from_image(Image.load_from_file(image)) for image in images])
                messages.append(Content(role="user", parts=parts))
                messages.append(Content(role="model", parts=[Part.from_text(history.get("text"))]))
                content = ""
                images.clear()

    last_message = messages.pop()
    chat = model.start_chat(history=messages)
    return chat, last_message


async def get_gemini(chat, message):
    responses = await chat.send_message_async(
        content=message,
        generation_config=generation_config,
        safety_settings=safety_settings,
        stream=True,
    )

    async for chunk in responses:
        chunk_message = chunk.text
        yield chunk_message if chunk_message else " "
    yield " "
