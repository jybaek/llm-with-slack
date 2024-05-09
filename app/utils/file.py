import base64
import requests
from app.config.constants import slack_token


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def download_file(url: str, filename):
    headers = {"Authorization": f"Bearer {slack_token}"} if "slack" in url else {}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        with open(filename, "wb") as f:
            f.write(r.content)
        return True
    else:
        return False
