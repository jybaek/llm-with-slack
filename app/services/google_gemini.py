import logging
import vertexai

from app.config.constants import number_of_messages_to_keep
from vertexai.generative_models import GenerativeModel, Content, Part
import vertexai.preview.generative_models as generative_models


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
    content = ""
    # 사용자와 모델이 메시지를 번갈아가면서 주고받지 않으면 오류가 발생하기 때문에 아래와 같은 처리를 함
    for history in chat_history[:-1]:
        role = "model" if "app_id" in history else "user"
        if role == "user":
            content += history.get("text")
        else:
            messages.append(Content(role="user", parts=[Part.from_text(content)]))
            messages.append(Content(role="model", parts=[Part.from_text(history.get("text"))]))
            content = ""

    chat = model.start_chat(history=messages)
    return chat, content


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
