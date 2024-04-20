import logging

from slack_sdk import WebClient
from app.config.constants import slack_token, gemini_slack_token, model, openai_token, LLMModel
from app.services.google_gemini import build_gemini_message, get_gemini
from app.services.openai_chat import get_chatgpt, Model, build_chatgpt_message
from app.utils.message import async_generator

gpt_slack_client = WebClient(token=slack_token)
gemini_slack_client = WebClient(token=gemini_slack_token if gemini_slack_token else slack_token)


async def message_process(slack_message: dict, llm_model: LLMModel):
    event = slack_message.get("event")
    channel = event.get("channel")
    thread_ts = event.get("thread_ts") if event.get("thread_ts") else event.get("ts")
    user = event.get("user")
    api_app_id = slack_message.get("api_app_id")

    try:
        if llm_model == LLMModel.GPT:
            slack_client = gpt_slack_client
            # Set the data to send
            messages = await build_chatgpt_message(slack_client, channel, thread_ts)

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
        elif llm_model == LLMModel.GEMINI:
            slack_client = gemini_slack_client
            chat, content = await build_gemini_message(slack_client, channel, thread_ts)
            response_message = get_gemini(chat, content)
        else:
            raise Exception(f"Error - Unknown model: {llm_model}")
    except Exception as e:
        response_message = async_generator(e.__str__())

    logging.info(f"[{thread_ts}][{api_app_id}:{channel}:{user}] request_message: {event.get('text')}")
    message = ts = ""
    try:
        async for chunk in response_message:
            message += chunk
            if not ts:
                result = slack_client.chat_postMessage(
                    channel=channel, text=message, thread_ts=thread_ts, attachments=[]
                )
                ts = result["ts"]
            else:
                # Logic to avoid Slack rate limits.
                if len(message) % 10 == 0 or (len(chunk) == 1 and chunk == " "):
                    slack_client.chat_update(channel=channel, text=message, ts=ts, as_user=True)
    except Exception as e:
        slack_client.chat_postMessage(channel=channel, text=str(e), thread_ts=thread_ts, attachments=[])

    logging.info(f"[{thread_ts}][{api_app_id}:{channel}:{user}] response_message: {message}")
