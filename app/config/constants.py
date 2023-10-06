import os


slack_token = os.environ.get("slack_token")
openai_token = os.environ.get("openai_token")
number_of_messages_to_keep = int(os.environ.get("number_of_messages_to_keep", "5"))
model = os.environ.get("model")
system_content = os.environ.get("system_content")
