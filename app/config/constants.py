import os
from enum import Enum

# For ChatGPT
slack_token = os.environ.get("slack_token")
openai_token = os.environ.get("openai_token")
gpt_model = os.environ.get("gpt_model", "gpt-3.5-turbo")

# For Gemini
google_cloud_project_name = os.environ.get("google_cloud_project_name")
gemini_slack_token = os.environ.get("gemini_slack_token")
gemini_model = os.environ.get("gemini_model", "gemini-1.5-pro-001")  # or gemini-1.5-flash-001
enable_grounding = os.environ.get("enable_grounding", False)

# Common
number_of_messages_to_keep = int(os.environ.get("number_of_messages_to_keep", "5"))
system_content = os.environ.get("system_content")

# Image
MAX_FILE_BYTES = int(os.environ.get("max_file_bytes", 1_000_000))


class LLMModel(Enum):
    GPT = "gpt"
    GEMINI = "gemini"
