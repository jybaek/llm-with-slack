import random

from fastapi import APIRouter, Header, Request
from starlette.background import BackgroundTasks
from starlette.responses import Response

from app.config.constants import LLMModel
from app.services.slack import message_process

router = APIRouter()


@router.post("/gpt")
async def slack(request: Request, message: dict, background_tasks: BackgroundTasks, headers=Header(default=None)):
    if message.get("challenge"):
        return message.get("challenge")

    if request.headers.get("x-slack-retry-num") and request.headers.get("x-slack-retry-reason") == "http_timeout":
        return Response("ok")
    else:
        # Because Slack is constrained to give a response in 3 seconds, ChatGPT processing is handled by background_tasks.
        background_tasks.add_task(message_process, message, LLMModel.GPT)
    return Response("ok")


@router.post("/gemini")
async def slack(request: Request, message: dict, background_tasks: BackgroundTasks):
    if message.get("challenge"):
        return message.get("challenge")
    if request.headers.get("x-slack-retry-num") and request.headers.get("x-slack-retry-reason") == "http_timeout":
        return Response("ok")
    else:
        # Because Slack is constrained to give a response in 3 seconds, ChatGPT processing is handled by background_tasks.
        background_tasks.add_task(message_process, message, LLMModel.GEMINI)
    return Response("ok")


@router.post("/random")
async def slack(request: Request, message: dict, background_tasks: BackgroundTasks):
    if message.get("challenge"):
        return message.get("challenge")
    if request.headers.get("x-slack-retry-num") and request.headers.get("x-slack-retry-reason") == "http_timeout":
        return Response("ok")
    else:
        llm_model = random.choices([LLMModel.GPT, LLMModel.GEMINI])[0]
        # Because Slack is constrained to give a response in 3 seconds, ChatGPT processing is handled by background_tasks.
        background_tasks.add_task(message_process, message, llm_model)
    return Response("ok")
