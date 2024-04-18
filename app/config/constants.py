import os
from enum import Enum

slack_token = os.environ.get("slack_token")  # ChatGPT
gemini_slack_token = os.environ.get("gemini_slack_token")
openai_token = os.environ.get("openai_token")
number_of_messages_to_keep = int(os.environ.get("number_of_messages_to_keep", "5"))
model = os.environ.get("model", "gpt-3.5-turbo")
system_content = os.environ.get("system_content")
MAX_FILE_BYTES = 1_000_000


class LLMModel(Enum):
    GPT = "gpt"
    GEMINI = "gemini"
