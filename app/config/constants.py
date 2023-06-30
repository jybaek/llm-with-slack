import os

redis_host = os.environ.get("REDIS_HOST", "localhost")
redis_port = int(os.environ.get("REDIS_PORT", 6379))

slack_token = os.environ.get("slack_token")
slack_token2 = os.environ.get("slack_token2")
openai_token = os.environ.get("openai_token")
number_of_messages_to_keep = int(os.environ.get("number_of_messages_to_keep", "0"))
model = os.environ.get("model")
system_content = os.environ.get("system_content")

MESSAGE_EXPIRE_TIME = 60 * 60 * 6
