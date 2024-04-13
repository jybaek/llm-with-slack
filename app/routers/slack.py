from fastapi import APIRouter
from starlette.background import BackgroundTasks
from starlette.responses import Response

from app.services.slack import message_process

router = APIRouter()


@router.post("")
async def slack(message: dict, background_tasks: BackgroundTasks):
    if message.get("challenge"):
        return message.get("challenge")

    # Because Slack is constrained to give a response in 3 seconds, ChatGPT processing is handled by background_tasks.
    background_tasks.add_task(message_process, message)
    return Response("ok")
